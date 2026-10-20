// Aevrynd-owned finite shaft capsule contact kernel, 2026.
// Same finite-feature/mass-weighted projection as the offline Python reference.
// Standard C++ only; no Blender, third-party solver, engine or asset dependency.
// This is an isolated CPU kernel, not a measured production engine integration.
#include <algorithm>
#include <array>
#include <bit>
#include <cmath>
#include <cstdint>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <utility>
#include <vector>
#ifdef _WIN32
#define AEV_API extern "C" __declspec(dllexport)
#else
#define AEV_API extern "C"
#endif
namespace {
struct V { double x,y,z; V operator+(V b)const{return{x+b.x,y+b.y,z+b.z};} V operator-(V b)const{return{x-b.x,y-b.y,z-b.z};} V operator*(double s)const{return{x*s,y*s,z*s};} };
double dot(V a,V b){return (a.x*b.x+a.y*b.y)+a.z*b.z;}
double norm(V a){return std::sqrt(dot(a,a));}
V cross(V a,V b){return{a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
V get(const double* p,int i){return{p[i*3],p[i*3+1],p[i*3+2]};}
void add(double* p,int i,V d){p[i*3]+=d.x;p[i*3+1]+=d.y;p[i*3+2]+=d.z;}
double value(V a,int axis){return axis==0?a.x:axis==1?a.y:a.z;}
struct Feature {double distance,s,t;};
Feature closest(V A,V B,V C,V D){
    V u=B-A,v=D-C,w=A-C;double a=dot(u,u),b=dot(u,v),c=dot(v,v),d=dot(u,w),e=dot(v,w),den=a*c-b*b;
    Feature best{std::numeric_limits<double>::infinity(),0,0};
    auto candidate=[&](double s,double t){double dist=norm(w+u*s-v*t);if(dist<best.distance)best={dist,s,t};};
    if(std::abs(den)>1e-26){double s=(b*e-c*d)/den,t=(a*e-b*d)/den;if(s>=0&&s<=1&&t>=0&&t<=1)candidate(s,t);}
    candidate(0,std::clamp(dot(A-C,v)/std::max(c,1e-30),0.,1.));candidate(1,std::clamp(dot(B-C,v)/std::max(c,1e-30),0.,1.));
    candidate(std::clamp(dot(C-A,u)/std::max(a,1e-30),0.,1.),0);candidate(std::clamp(dot(D-A,u)/std::max(a,1e-30),0.,1.),1);return best;
}
double planeGap(V A,V B,V C,V D,double radius){
    V tangent=(B-A)+(D-C);tangent=tangent*(1/std::max(norm(tangent),1e-30));V delta=((A+B)-(C+D))*.5;V axis=delta-tangent*dot(delta,tangent);
    if(norm(axis)<1e-16)axis=delta;if(norm(axis)<1e-20)axis={1,0,0};axis=axis*(1/std::max(norm(axis),1e-30));
    return std::abs(dot(delta,axis))-.5*(std::abs(dot(B-A,axis))+std::abs(dot(D-C,axis)))-radius;
}
struct Segment{int a,b;double r;V lo,hi;};
struct Contact{int first,second;std::array<int,4> vertex;};
}
struct ShaftContactStats{std::int64_t candidates,active,corrections,colours;double minimumGap;};
AEV_API int aevrynd_shaft_contact_abi(){return static_cast<int>(sizeof(ShaftContactStats));}
AEV_API int aevrynd_shaft_contacts(double* positions,const double* radii,const double* inverseMass,int fibres,int points,double designGap,double solveResidual,ShaftContactStats* stats){
    try{
        if(!positions||!radii||!inverseMass||!stats||fibres<1||points<2)return -1;
        *stats={0,0,0,0,std::numeric_limits<double>::infinity()};int per=points-1,total=fibres*per;
        std::vector<Segment> segments;segments.reserve(total);V globalLo{1e30,1e30,1e30},globalHi{-1e30,-1e30,-1e30},span{};
        for(int f=0;f<fibres;++f)for(int j=0;j<per;++j){int a=f*points+j,b=a+1;V A=get(positions,a),B=get(positions,b);double r=std::max(radii[a],radii[b]),pad=(r+designGap*.5)+.0000005;V lo{std::min(A.x,B.x)-pad,std::min(A.y,B.y)-pad,std::min(A.z,B.z)-pad},hi{std::max(A.x,B.x)+pad,std::max(A.y,B.y)+pad,std::max(A.z,B.z)+pad};segments.push_back({a,b,r,lo,hi});globalLo={std::min(globalLo.x,lo.x),std::min(globalLo.y,lo.y),std::min(globalLo.z,lo.z)};globalHi={std::max(globalHi.x,hi.x),std::max(globalHi.y,hi.y),std::max(globalHi.z,hi.z)};span=span+(hi-lo);}
        int axis=0;double score=-1;
        for(int k=0;k<3;++k){double s=value(globalHi-globalLo,k)/std::max(value(span,k)/total,1e-12);if(s>score){score=s;axis=k;}}
        std::vector<int> order(total);std::iota(order.begin(),order.end(),0);std::stable_sort(order.begin(),order.end(),[&](int a,int b){return value(segments[a].lo,axis)<value(segments[b].lo,axis);});
        std::vector<std::pair<int,int>> pairs;
        for(int a=0;a<total;++a){int ia=order[a];const auto&A=segments[ia];for(int b=a+1;b<total;++b){int ib=order[b];const auto&B=segments[ib];if(value(B.lo,axis)>value(A.hi,axis))break;if(ia/per==ib/per&&std::abs(ia-ib)<=1)continue;if(A.lo.x>B.hi.x||B.lo.x>A.hi.x||A.lo.y>B.hi.y||B.lo.y>A.hi.y||A.lo.z>B.hi.z||B.lo.z>A.hi.z)continue;pairs.emplace_back(std::min(ia,ib),std::max(ia,ib));}}
        std::sort(pairs.begin(),pairs.end());stats->candidates=static_cast<std::int64_t>(pairs.size());std::vector<Contact> active;
        for(auto [ia,ib]:pairs){const auto&A=segments[ia];const auto&B=segments[ib];V a=get(positions,A.a),b=get(positions,A.b),c=get(positions,B.a),d=get(positions,B.b);if(planeGap(a,b,c,d,A.r+B.r+designGap)>0)continue;Feature f=closest(a,b,c,d);double gap=f.distance-A.r-B.r;stats->minimumGap=std::min(stats->minimumGap,gap);if(gap<designGap-solveResidual)active.push_back({ia,ib,{A.a,A.b,B.a,B.b}});}
        stats->active=static_cast<std::int64_t>(active.size());std::vector<std::array<std::uint64_t,4>> used(fibres*points);std::vector<std::vector<int>> colours;
        for(int row=0;row<static_cast<int>(active.size());++row){auto v=active[row].vertex;int colour=-1,word=0,bit=0;for(word=0;word<4;++word){std::uint64_t blocked=used[v[0]][word]|used[v[1]][word]|used[v[2]][word]|used[v[3]][word];if(blocked!=UINT64_MAX){std::uint64_t first=(~blocked)&(blocked+1);bit=std::countr_zero(first);colour=word*64+bit;break;}}if(colour<0)return -3;if(static_cast<int>(colours.size())<=colour)colours.resize(colour+1);colours[colour].push_back(row);for(int vertex:v)used[vertex][word]|=std::uint64_t{1}<<bit;}
        stats->colours=static_cast<std::int64_t>(colours.size());
        for(const auto&group:colours)for(int row:group){const auto&contact=active[row];const auto&A=segments[contact.first];const auto&B=segments[contact.second];V a=get(positions,A.a),b=get(positions,A.b),c=get(positions,B.a),d=get(positions,B.b);Feature f=closest(a,b,c,d);double target=A.r+B.r+designGap;if(f.distance>=target-solveResidual)continue;V normal=(a+(b-a)*f.s)-(c+(d-c)*f.t);
            if(f.distance<1e-12){normal=cross(b-a,d-c);if(norm(normal)<1e-12)normal=cross(b-a,{1.,.371,.193});normal=normal*(1/std::max(norm(normal),1e-20));}else normal=normal*(1/f.distance);
            std::array<double,4> factor{1-f.s,f.s,-(1-f.t),-f.t};double den=0;for(int k=0;k<4;++k)den+=(inverseMass[contact.vertex[k]]*factor[k])*factor[k];if(!(den>0))return -4;double dl=(target-f.distance)/den;
            for(int k=0;k<4;++k){double scale=inverseMass[contact.vertex[k]]*factor[k];add(positions,contact.vertex[k],(normal*scale)*dl);}++stats->corrections;
        }
        return 0;
    }catch(...){return -9;}
}

// Speculative continuous contact. A closest-feature normal of the accepted old
// segments separates all their points. Requiring every new endpoint difference
// to remain on that same positive side certifies the complete linear movement,
// since all simultaneous segment-point differences are convex combinations.
struct ShaftSweepStats{std::int64_t candidates,corrections,unqualifiedPairs;double minimumOldGap,minimumNewPlaneGap;};
namespace {
struct SweepPair{int a,b,c,d;double radius;V normal;double oldGap;};
std::vector<SweepPair> sweepPairs(const double*old,const double*next,const double*radii,int fibres,int points){
    int per=points-1,total=fibres*per;std::vector<Segment>s;V low{1e30,1e30,1e30},high{-1e30,-1e30,-1e30},span{};s.reserve(total);
    for(int f=0;f<fibres;++f)for(int j=0;j<per;++j){int a=f*points+j,b=a+1;V A=get(old,a),B=get(old,b),C=get(next,a),D=get(next,b);double r=std::max(radii[a],radii[b]),pad=r+.000002;V lo{std::min({A.x,B.x,C.x,D.x})-pad,std::min({A.y,B.y,C.y,D.y})-pad,std::min({A.z,B.z,C.z,D.z})-pad},hi{std::max({A.x,B.x,C.x,D.x})+pad,std::max({A.y,B.y,C.y,D.y})+pad,std::max({A.z,B.z,C.z,D.z})+pad};s.push_back({a,b,r,lo,hi});low={std::min(low.x,lo.x),std::min(low.y,lo.y),std::min(low.z,lo.z)};high={std::max(high.x,hi.x),std::max(high.y,hi.y),std::max(high.z,hi.z)};span=span+(hi-lo);}
    int axis=0;double score=-1;for(int k=0;k<3;++k){double v=value(high-low,k)/std::max(value(span,k)/total,1e-12);if(v>score){score=v;axis=k;}}
    std::vector<int> order(total);std::iota(order.begin(),order.end(),0);std::stable_sort(order.begin(),order.end(),[&](int a,int b){return value(s[a].lo,axis)<value(s[b].lo,axis);});std::vector<std::pair<int,int>>indices;
    for(int a=0;a<total;++a){int ia=order[a];const auto&A=s[ia];for(int b=a+1;b<total;++b){int ib=order[b];const auto&B=s[ib];if(value(B.lo,axis)>value(A.hi,axis))break;if(ia/per==ib/per&&std::abs(ia-ib)<=1)continue;if(A.lo.x>B.hi.x||B.lo.x>A.hi.x||A.lo.y>B.hi.y||B.lo.y>A.hi.y||A.lo.z>B.hi.z||B.lo.z>A.hi.z)continue;indices.emplace_back(std::min(ia,ib),std::max(ia,ib));}}
    std::sort(indices.begin(),indices.end());std::vector<SweepPair>out;out.reserve(indices.size());
    for(auto [i,j]:indices){const auto&A=s[i];const auto&B=s[j];V a=get(old,A.a),b=get(old,A.b),c=get(old,B.a),d=get(old,B.b);Feature feature=closest(a,b,c,d);if(!(feature.distance>1e-12))throw std::runtime_error("Invalid old shaft separation");V n=((a+(b-a)*feature.s)-(c+(d-c)*feature.t))*(1/feature.distance);out.push_back({A.a,A.b,B.a,B.b,A.r+B.r,n,feature.distance-A.r-B.r});}
    return out;
}
double newPlaneGap(const SweepPair&p,const double*x){double smallest=std::min(dot(get(x,p.a),p.normal),dot(get(x,p.b),p.normal));double biggest=std::max(dot(get(x,p.c),p.normal),dot(get(x,p.d),p.normal));return smallest-biggest-p.radius;}
}
AEV_API int aevrynd_shaft_sweep_abi(){return static_cast<int>(sizeof(ShaftSweepStats));}
AEV_API int aevrynd_shaft_sweep(const double*old,double*next,const double*radii,const double*inverseMass,int fibres,int points,double designGap,double solveResidual,double oldSafety,double newSafety,int project,ShaftSweepStats*stats){
    try{
        if(!old||!next||!radii||!inverseMass||!stats||fibres<1||points<2)return -1;*stats={0,0,0,std::numeric_limits<double>::infinity(),std::numeric_limits<double>::infinity()};auto pairs=sweepPairs(old,next,radii,fibres,points);stats->candidates=static_cast<std::int64_t>(pairs.size());
        if(project)for(const auto&p:pairs){if(p.oldGap<=oldSafety)return -6;if(newPlaneGap(p,next)>=designGap-solveResidual)continue;for(int a:{p.a,p.b})for(int b:{p.c,p.d}){double gap=dot(get(next,a)-get(next,b),p.normal)-p.radius;if(gap>=designGap-solveResidual)continue;double den=inverseMass[a]+inverseMass[b];if(!(den>0))return -4;double dl=(designGap-gap)/den;add(next,a,p.normal*(inverseMass[a]*dl));add(next,b,p.normal*(-inverseMass[b]*dl));++stats->corrections;}}
        // Rebuild swept broad phase after projection: corrections may create new
        // neighbours. No cached candidate set is treated as a complete proof.
        if(project)pairs=sweepPairs(old,next,radii,fibres,points);
        for(const auto&p:pairs){double gap=newPlaneGap(p,next);stats->minimumOldGap=std::min(stats->minimumOldGap,p.oldGap);stats->minimumNewPlaneGap=std::min(stats->minimumNewPlaneGap,gap);if(p.oldGap<=oldSafety||gap<newSafety)++stats->unqualifiedPairs;}
        return 0;
    }catch(...){return -9;}
}
