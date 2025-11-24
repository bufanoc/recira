/*
	Copyright (c) 2004-2013, The Dojo Foundation All Rights Reserved.
	Available via Academic Free License >= 2.1 OR the modified BSD license.
	see: http://dojotoolkit.org/license for details
*/


if(!dojo._hasResource["dijit.layout._LayoutWidget"]){
dojo._hasResource["dijit.layout._LayoutWidget"]=true;
dojo.provide("dijit.layout._LayoutWidget");
dojo.require("dijit._Widget");
dojo.require("dijit._Container");
dojo.require("dijit._Contained");
dojo.declare("dijit.layout._LayoutWidget",[dijit._Widget,dijit._Container,dijit._Contained],{baseClass:"dijitLayoutContainer",isLayoutContainer:true,postCreate:function(){
dojo.addClass(this.domNode,"dijitContainer");
dojo.addClass(this.domNode,this.baseClass);
this.inherited(arguments);
},startup:function(){
if(this._started){
return;
}
this.inherited(arguments);
var _1=this.getParent&&this.getParent();
if(!(_1&&_1.isLayoutContainer)){
this.resize();
this.connect(dojo.isIE?this.domNode:dojo.global,"onresize",function(){
this.resize();
});
}
},resize:function(_2,_3){
var _4=this.domNode;
if(_2){
dojo.marginBox(_4,_2);
if(_2.t){
_4.style.top=_2.t+"px";
}
if(_2.l){
_4.style.left=_2.l+"px";
}
}
var mb=_3||{};
dojo.mixin(mb,_2||{});
if(!("h" in mb)||!("w" in mb)){
mb=dojo.mixin(dojo.marginBox(_4),mb);
}
var cs=dojo.getComputedStyle(_4);
var me=dojo._getMarginExtents(_4,cs);
var be=dojo._getBorderExtents(_4,cs);
var bb=(this._borderBox={w:mb.w-(me.w+be.w),h:mb.h-(me.h+be.h)});
var pe=dojo._getPadExtents(_4,cs);
this._contentBox={l:dojo._toPixelValue(_4,cs.paddingLeft),t:dojo._toPixelValue(_4,cs.paddingTop),w:bb.w-pe.w,h:bb.h-pe.h};
this.layout();
},layout:function(){
},_setupChild:function(_5){
dojo.addClass(_5.domNode,this.baseClass+"-child");
if(_5.baseClass){
dojo.addClass(_5.domNode,this.baseClass+"-"+_5.baseClass);
}
},addChild:function(_6,_7){
this.inherited(arguments);
if(this._started){
this._setupChild(_6);
}
},removeChild:function(_8){
dojo.removeClass(_8.domNode,this.baseClass+"-child");
if(_8.baseClass){
dojo.removeClass(_8.domNode,this.baseClass+"-"+_8.baseClass);
}
this.inherited(arguments);
}});
dijit.layout.marginBox2contentBox=function(_9,mb){
var cs=dojo.getComputedStyle(_9);
var me=dojo._getMarginExtents(_9,cs);
var pb=dojo._getPadBorderExtents(_9,cs);
return {l:dojo._toPixelValue(_9,cs.paddingLeft),t:dojo._toPixelValue(_9,cs.paddingTop),w:mb.w-(me.w+pb.w),h:mb.h-(me.h+pb.h)};
};
(function(){
var _a=function(_b){
return _b.substring(0,1).toUpperCase()+_b.substring(1);
};
var _c=function(_d,_e){
var _f=_d.resize?_d.resize(_e):dojo.marginBox(_d.domNode,_e);
if(_f){
dojo.mixin(_d,_f);
}else{
dojo.mixin(_d,dojo.marginBox(_d.domNode));
dojo.mixin(_d,_e);
}
};
dijit.layout.layoutChildren=function(_10,dim,_11){
dim=dojo.mixin({},dim);
dojo.addClass(_10,"dijitLayoutContainer");
_11=dojo.filter(_11,function(_12){
return _12.layoutAlign!="client";
}).concat(dojo.filter(_11,function(_13){
return _13.layoutAlign=="client";
}));
dojo.forEach(_11,function(_14){
var elm=_14.domNode,pos=_14.layoutAlign;
var _15=elm.style;
_15.left=dim.l+"px";
_15.top=dim.t+"px";
_15.position="absolute";
dojo.addClass(elm,"dijitAlign"+_a(pos));
if(pos=="top"||pos=="bottom"){
_c(_14,{w:dim.w});
dim.h-=_14.h;
if(pos=="top"){
dim.t+=_14.h;
}else{
_15.top=dim.t+dim.h+"px";
}
}else{
if(pos=="left"||pos=="right"){
_c(_14,{h:dim.h});
dim.w-=_14.w;
if(pos=="left"){
dim.l+=_14.w;
}else{
_15.left=dim.l+dim.w+"px";
}
}else{
if(pos=="client"){
_c(_14,dim);
}
}
}
});
};
})();
}
