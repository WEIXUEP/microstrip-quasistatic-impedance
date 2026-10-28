export async function mesh(gmsh, p) {
  gmsh.initialize();
  try {
    gmsh.option.setNumber('General.Terminal', 0);
    gmsh.model.add('microstrip');
    const h=p.h1+p.h2, halfSub=15*h, halfAir=25*h;
    const occ=gmsh.model.occ;
    const air=occ.addRectangle(-halfAir,-2*h,0,2*halfAir,13*h);
    const lower=occ.addRectangle(-halfSub,0,0,2*halfSub,p.h1);
    const upper=occ.addRectangle(-halfSub,p.h1,0,2*halfSub,p.h2);
    const bottom=p.h1, top=p.h1+p.trace_thickness, w=Math.max(p.w1,p.w2);
    const points=[[-p.w1/2,bottom],[p.w1/2,bottom],[p.w2/2,top],[-p.w2/2,top]].map(([x,y])=>occ.addPoint(x,y,0));
    const lines=points.map((v,i)=>occ.addLine(v,points[(i+1)%4]));
    const trace=occ.addPlaneSurface([occ.addCurveLoop(lines)]);
    occ.fragment([2,air,2,lower,2,upper,2,trace],[]);
    occ.synchronize();
    const surfaces=[], signal=[], ground=[], tol=1e-5;
    const entities=(dim)=>{const a=gmsh.model.getEntities(dim); return a.dimTags ?? a;};
    for (let a=entities(2),i=0;i<a.length;i+=2) {
      const tag=a[i+1], b=gmsh.model.getBoundingBox(2,tag), x=(b.xmin+b.xmax)/2, y=(b.ymin+b.ymax)/2;
      if (b.xmin>=-w/2-tol && b.xmax<=w/2+tol && b.ymin>=bottom-tol && b.ymax<=top+tol) continue;
      const kind=Math.abs(x)<=halfSub+tol && y>=-tol && y<=h+tol ? (y<p.h1?'lower':'upper'):'air';
      surfaces.push([tag,kind]);
    }
    for (let a=entities(1),i=0;i<a.length;i+=2) {
      const tag=a[i+1], b=gmsh.model.getBoundingBox(1,tag), y=(b.ymin+b.ymax)/2;
      const inside=b.xmin>=-w/2-tol && b.xmax<=w/2+tol && b.ymin>=bottom-tol && b.ymax<=top+tol;
      if (inside && (Math.abs(y-bottom)<tol || Math.abs(y-top)<tol || b.ymax-b.ymin>tol)) signal.push(tag);
      else if (b.ymax-b.ymin<tol && Math.abs(y)<tol && b.xmin>=-halfSub-tol && b.xmax<=halfSub+tol) ground.push(tag);
    }
    if (!signal.length || !ground.length) throw new Error('Cannot identify conductor boundaries');
    const f=gmsh.model.mesh.field;
    f.add('Distance',1); f.setNumbers(1,'CurvesList',signal.concat(ground)); f.setNumber(1,'Sampling',150);
    f.add('Threshold',2); f.setNumber(2,'InField',1);
    f.setNumber(2,'SizeMin',Math.sqrt((p.w1+p.w2)*p.trace_thickness/2/p.trace_mesh_area_factor));
    f.setNumber(2,'SizeMax',Math.sqrt(50*h*13*h/p.far_mesh_area_factor));
    f.setNumber(2,'DistMin',.5*p.trace_thickness); f.setNumber(2,'DistMax',8*Math.max(p.h1,p.h2,w)); f.setAsBackgroundMesh(2);
    for(const key of ['Mesh.MeshSizeExtendFromBoundary','Mesh.MeshSizeFromPoints','Mesh.MeshSizeFromCurvature']) gmsh.option.setNumber(key,0);
    gmsh.option.setNumber('Mesh.Algorithm',6); gmsh.model.mesh.generate(2);
    const all=gmsh.model.mesh.getNodes(), indexes=new Map(all.nodeTags.map((tag,i)=>[tag,i]));
    const triangles=[], er=[];
    for (const [tag,kind] of surfaces) {
      const e=gmsh.model.mesh.getElements(2,tag);
      for(let i=0;i<e.elementTypes.length;i++) {
        if(gmsh.model.mesh.getElementProperties(e.elementTypes[i]).numNodes!==3) throw Error('Expected linear triangles');
        const n=e.nodeTags[i]; for(let j=0;j<n.length;j+=3) { triangles.push(n.slice(j,j+3).map(v=>indexes.get(v))); er.push(kind==='lower'?p.er1:kind==='upper'?p.er2:1); }
      }
    }
    const boundary=(curves)=>[...new Set(curves.flatMap(tag=>gmsh.model.mesh.getNodes(1,tag,true).nodeTags.map(v=>indexes.get(v))))];
    return {points:Array.from({length:all.nodeTags.length},(_,i)=>[all.coord[i*3]*25.4e-6,all.coord[i*3+1]*25.4e-6]),triangles,er,signal:boundary(signal),ground:boundary(ground)};
  } finally { gmsh.finalize(); }
}
