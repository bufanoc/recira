/*
	Copyright (c) 2004-2013, The Dojo Foundation All Rights Reserved.
	Available via Academic Free License >= 2.1 OR the modified BSD license.
	see: http://dojotoolkit.org/license for details
*/


if(!dojo._hasResource["dijit._editor.RichText"]){
dojo._hasResource["dijit._editor.RichText"]=true;
dojo.provide("dijit._editor.RichText");
dojo.require("dijit._Widget");
dojo.require("dijit._editor.selection");
dojo.require("dijit._editor.range");
dojo.require("dijit._editor.html");
if(!dojo.config["useXDomain"]||dojo.config["allowXdRichTextSave"]){
if(dojo._postLoad){
(function(){
var _1=dojo.doc.createElement("textarea");
_1.id=dijit._scopeName+"._editor.RichText.savedContent";
dojo.style(_1,{display:"none",position:"absolute",top:"-100px",height:"3px",width:"3px"});
dojo.body().appendChild(_1);
})();
}else{
try{
dojo.doc.write("<textarea id=\""+dijit._scopeName+"._editor.RichText.savedContent\" "+"style=\"display:none;position:absolute;top:-100px;left:-100px;height:3px;width:3px;overflow:hidden;\"></textarea>");
}
catch(e){
}
}
}
dojo.declare("dijit._editor.RichText",dijit._Widget,{constructor:function(_2){
this.contentPreFilters=[];
this.contentPostFilters=[];
this.contentDomPreFilters=[];
this.contentDomPostFilters=[];
this.editingAreaStyleSheets=[];
this.events=[].concat(this.events);
this._keyHandlers={};
this.onLoadDeferred=new dojo.Deferred();
},inheritWidth:false,focusOnLoad:false,name:"",styleSheets:"",_content:"",height:"300px",minHeight:"1em",isClosed:true,isLoaded:false,_SEPARATOR:"@@**%%__RICHTEXTBOUNDRY__%%**@@",onLoadDeferred:null,isTabIndent:false,disableSpellCheck:false,postCreate:function(){
if("textarea"==this.domNode.tagName.toLowerCase()){
console.warn("RichText should not be used with the TEXTAREA tag.  See dijit._editor.RichText docs.");
}
this.contentPreFilters=[dojo.hitch(this,"_preFixUrlAttributes")].concat(this.contentPreFilters);
if(dojo.isMoz){
this.contentPreFilters=[this._normalizeFontStyle].concat(this.contentPreFilters);
this.contentPostFilters=[this._removeMozBogus].concat(this.contentPostFilters);
}
if(dojo.isWebKit){
this.contentPreFilters=[this._removeWebkitBogus].concat(this.contentPreFilters);
this.contentPostFilters=[this._removeWebkitBogus].concat(this.contentPostFilters);
}
if(dojo.isIE){
this.contentPostFilters=[this._normalizeFontStyle].concat(this.contentPostFilters);
}
dojo.publish(dijit._scopeName+"._editor.RichText::init",[this]);
this.open();
this.setupDefaultShortcuts();
},setupDefaultShortcuts:function(){
var _3=dojo.hitch(this,function(_4,_5){
return function(){
return !this.execCommand(_4,_5);
};
});
var _6={b:_3("bold"),i:_3("italic"),u:_3("underline"),a:_3("selectall"),s:function(){
this.save(true);
},m:function(){
this.isTabIndent=!this.isTabIndent;
},"1":_3("formatblock","h1"),"2":_3("formatblock","h2"),"3":_3("formatblock","h3"),"4":_3("formatblock","h4"),"\\":_3("insertunorderedlist")};
if(!dojo.isIE){
_6.Z=_3("redo");
}
for(var _7 in _6){
this.addKeyHandler(_7,true,false,_6[_7]);
}
},events:["onKeyPress","onKeyDown","onKeyUp","onClick"],captureEvents:[],_editorCommandsLocalized:false,_localizeEditorCommands:function(){
if(dijit._editor._editorCommandsLocalized){
this._local2NativeFormatNames=dijit._editor._local2NativeFormatNames;
this._native2LocalFormatNames=dijit._editor._native2LocalFormatNames;
return;
}
dijit._editor._editorCommandsLocalized=true;
dijit._editor._local2NativeFormatNames={};
dijit._editor._native2LocalFormatNames={};
this._local2NativeFormatNames=dijit._editor._local2NativeFormatNames;
this._native2LocalFormatNames=dijit._editor._native2LocalFormatNames;
var _8=["div","p","pre","h1","h2","h3","h4","h5","h6","ol","ul","address"];
var _9="",_a,i=0;
while((_a=_8[i++])){
if(_a.charAt(1)!=="l"){
_9+="<"+_a+"><span>content</span></"+_a+"><br/>";
}else{
_9+="<"+_a+"><li>content</li></"+_a+"><br/>";
}
}
var _b={position:"absolute",top:"0px",zIndex:10,opacity:0.01};
var _c=dojo.create("div",{style:_b,innerHTML:_9});
dojo.body().appendChild(_c);
var _d=dojo.hitch(this,function(){
var _e=_c.firstChild;
while(_e){
try{
dijit._editor.selection.selectElement(_e.firstChild);
var _f=_e.tagName.toLowerCase();
this._local2NativeFormatNames[_f]=document.queryCommandValue("formatblock");
this._native2LocalFormatNames[this._local2NativeFormatNames[_f]]=_f;
_e=_e.nextSibling.nextSibling;
}
catch(e){
}
}
_c.parentNode.removeChild(_c);
_c.innerHTML="";
});
setTimeout(_d,0);
},open:function(_10){
if(!this.onLoadDeferred||this.onLoadDeferred.fired>=0){
this.onLoadDeferred=new dojo.Deferred();
}
if(!this.isClosed){
this.close();
}
dojo.publish(dijit._scopeName+"._editor.RichText::open",[this]);
this._content="";
if(arguments.length==1&&_10.nodeName){
this.domNode=_10;
}
var dn=this.domNode;
var _11;
if(dn.nodeName&&dn.nodeName.toLowerCase()=="textarea"){
var ta=(this.textarea=dn);
this.name=ta.name;
_11=ta.value;
dn=this.domNode=dojo.doc.createElement("div");
dn.setAttribute("widgetId",this.id);
ta.removeAttribute("widgetId");
dn.cssText=ta.cssText;
dn.className+=" "+ta.className;
dojo.place(dn,ta,"before");
var _12=dojo.hitch(this,function(){
dojo.style(ta,{display:"block",position:"absolute",top:"-1000px"});
if(dojo.isIE){
var s=ta.style;
this.__overflow=s.overflow;
s.overflow="hidden";
}
});
if(dojo.isIE){
setTimeout(_12,10);
}else{
_12();
}
if(ta.form){
dojo.connect(ta.form,"onsubmit",this,function(){
ta.value=this.getValue();
});
}
}else{
_11=dijit._editor.getChildrenHtml(dn);
dn.innerHTML="";
}
var _13=dojo.contentBox(dn);
this._oldHeight=_13.h;
this._oldWidth=_13.w;
this.savedContent=_11;
if(dn.nodeName&&dn.nodeName=="LI"){
dn.innerHTML=" <br>";
}
this.editingArea=dn.ownerDocument.createElement("div");
dn.appendChild(this.editingArea);
if(this.name!==""&&(!dojo.config["useXDomain"]||dojo.config["allowXdRichTextSave"])){
var _14=dojo.byId(dijit._scopeName+"._editor.RichText.savedContent");
if(_14.value!==""){
var _15=_14.value.split(this._SEPARATOR),i=0,dat;
while((dat=_15[i++])){
var _16=dat.split(":");
if(_16[0]==this.name){
_11=_16[1];
_15.splice(i,1);
break;
}
}
}
dojo.addOnUnload(dojo.hitch(this,"_saveContent"));
}
this.isClosed=false;
var ifr=(this.editorObject=this.iframe=dojo.doc.createElement("iframe"));
ifr.id=this.id+"_iframe";
this._iframeSrc=this._getIframeDocTxt();
ifr.style.border="none";
ifr.style.width="100%";
if(this._layoutMode){
ifr.style.height="100%";
}else{
if(dojo.isIE>=7){
if(this.height){
ifr.style.height=this.height;
}
if(this.minHeight){
ifr.style.minHeight=this.minHeight;
}
}else{
ifr.style.height=this.height?this.height:this.minHeight;
}
}
ifr.frameBorder=0;
ifr._loadFunc=dojo.hitch(this,function(win){
this.window=win;
this.document=this.window.document;
if(dojo.isIE){
this._localizeEditorCommands();
}
this.onLoad(_11);
this.savedContent=this.getValue(true);
});
var s="javascript:parent."+dijit._scopeName+".byId(\""+this.id+"\")._iframeSrc";
ifr.setAttribute("src",s);
this.editingArea.appendChild(ifr);
if(dojo.isSafari){
setTimeout(function(){
ifr.setAttribute("src",s);
},0);
}
if(dn.nodeName=="LI"){
dn.lastChild.style.marginTop="-1.2em";
}
dojo.addClass(this.domNode,"RichTextEditable");
},_local2NativeFormatNames:{},_native2LocalFormatNames:{},_getIframeDocTxt:function(){
var _17=dojo.getComputedStyle(this.domNode);
var _18="";
if(dojo.isIE||(!this.height&&!dojo.isMoz)){
_18="<div></div>";
}else{
if(dojo.isMoz){
this._cursorToStart=true;
_18="&nbsp;";
}
}
var _19=[_17.fontWeight,_17.fontSize,_17.fontFamily].join(" ");
var _1a=_17.lineHeight;
if(_1a.indexOf("px")>=0){
_1a=parseFloat(_1a)/parseFloat(_17.fontSize);
}else{
if(_1a.indexOf("em")>=0){
_1a=parseFloat(_1a);
}else{
_1a="normal";
}
}
var _1b="";
this.style.replace(/(^|;)(line-|font-?)[^;]+/g,function(_1c){
_1b+=_1c.replace(/^;/g,"")+";";
});
var _1d=dojo.query("label[for=\""+this.id+"\"]");
return [this.isLeftToRight()?"<html><head>":"<html dir='rtl'><head>",(dojo.isMoz&&_1d.length?"<title>"+_1d[0].innerHTML+"</title>":""),"<meta http-equiv='Content-Type' content='text/html'>","<style>","body,html {","\tbackground:transparent;","\tpadding: 1px 0 0 0;","\tmargin: -1px 0 0 0;",(dojo.isWebKit?"\twidth: 100%;":""),(dojo.isWebKit?"\theight: 100%;":""),"}","body{","\ttop:0px; left:0px; right:0px;","\tfont:",_19,";",((this.height||dojo.isOpera)?"":"position: fixed;"),"\tmin-height:",this.minHeight,";","\tline-height:",_1a,"}","p{ margin: 1em 0; }",(this.height?"":"body,html{overflow-y:hidden;/*for IE*/} body > div {overflow-x:auto;/*FF:horizontal scrollbar*/ overflow-y:hidden;/*safari*/ min-height:"+this.minHeight+";/*safari*/}"),"li > ul:-moz-first-node, li > ol:-moz-first-node{ padding-top: 1.2em; } ",(!dojo.isIE?"li{ min-height:1.2em; }":""),"</style>",this._applyEditingAreaStyleSheets(),"</head><body onload='frameElement._loadFunc(window,document)' style='"+_1b+"'>",_18,"</body></html>"].join("");
},_applyEditingAreaStyleSheets:function(){
var _1e=[];
if(this.styleSheets){
_1e=this.styleSheets.split(";");
this.styleSheets="";
}
_1e=_1e.concat(this.editingAreaStyleSheets);
this.editingAreaStyleSheets=[];
var _1f="",i=0,url;
while((url=_1e[i++])){
var _20=(new dojo._Url(dojo.global.location,url)).toString();
this.editingAreaStyleSheets.push(_20);
_1f+="<link rel=\"stylesheet\" type=\"text/css\" href=\""+_20+"\"/>";
}
return _1f;
},addStyleSheet:function(uri){
var url=uri.toString();
if(url.charAt(0)=="."||(url.charAt(0)!="/"&&!uri.host)){
url=(new dojo._Url(dojo.global.location,url)).toString();
}
if(dojo.indexOf(this.editingAreaStyleSheets,url)>-1){
return;
}
this.editingAreaStyleSheets.push(url);
this.onLoadDeferred.addCallback(dojo.hitch(this,function(){
if(this.document.createStyleSheet){
this.document.createStyleSheet(url);
}else{
var _21=this.document.getElementsByTagName("head")[0];
var _22=this.document.createElement("link");
_22.rel="stylesheet";
_22.type="text/css";
_22.href=url;
_21.appendChild(_22);
}
}));
},removeStyleSheet:function(uri){
var url=uri.toString();
if(url.charAt(0)=="."||(url.charAt(0)!="/"&&!uri.host)){
url=(new dojo._Url(dojo.global.location,url)).toString();
}
var _23=dojo.indexOf(this.editingAreaStyleSheets,url);
if(_23==-1){
return;
}
delete this.editingAreaStyleSheets[_23];
dojo.withGlobal(this.window,"query",dojo,["link:[href=\""+url+"\"]"]).orphan();
},disabled:false,_mozSettingProps:{"styleWithCSS":false},_setDisabledAttr:function(_24){
this.disabled=_24;
if(!this.isLoaded){
return;
}
_24=!!_24;
if(dojo.isIE||dojo.isWebKit||dojo.isOpera){
var _25=dojo.isIE&&(this.isLoaded||!this.focusOnLoad);
if(_25){
this.editNode.unselectable="on";
}
this.editNode.contentEditable=!_24;
if(_25){
var _26=this;
setTimeout(function(){
_26.editNode.unselectable="off";
},0);
}
}else{
try{
this.document.designMode=(_24?"off":"on");
}
catch(e){
return;
}
if(!_24&&this._mozSettingProps){
var ps=this._mozSettingProps;
for(var n in ps){
if(ps.hasOwnProperty(n)){
try{
this.document.execCommand(n,false,ps[n]);
}
catch(e2){
}
}
}
}
}
this._disabledOK=true;
},onLoad:function(_27){
if(!this.window.__registeredWindow){
this.window.__registeredWindow=true;
this._iframeRegHandle=dijit.registerIframe(this.iframe);
}
if(!dojo.isIE&&(this.height||dojo.isMoz)){
this.editNode=this.document.body;
}else{
this.editNode=this.document.body.firstChild;
var _28=this;
if(dojo.isIE){
this.tabStop=dojo.create("div",{tabIndex:-1},this.editingArea);
this.iframe.onfocus=function(){
_28.editNode.setActive();
};
}
}
this.focusNode=this.editNode;
var _29=this.events.concat(this.captureEvents);
var ap=this.iframe?this.document:this.editNode;
dojo.forEach(_29,function(_2a){
this.connect(ap,_2a.toLowerCase(),_2a);
},this);
if(dojo.isIE){
this.connect(this.document,"onmousedown","_onIEMouseDown");
this.editNode.style.zoom=1;
}
if(dojo.isWebKit){
this._webkitListener=this.connect(this.document,"onmouseup","onDisplayChanged");
}
if(dojo.isIE){
try{
this.document.execCommand("RespectVisibilityInDesign",true,null);
}
catch(e){
}
}
this.isLoaded=true;
this.attr("disabled",this.disabled);
this.setValue(_27);
if(this.onLoadDeferred){
this.onLoadDeferred.callback(true);
}
this.onDisplayChanged();
if(this.focusOnLoad){
dojo.addOnLoad(dojo.hitch(this,function(){
setTimeout(dojo.hitch(this,"focus"),this.updateInterval);
}));
}
},onKeyDown:function(e){
if(e.keyCode===dojo.keys.TAB&&this.isTabIndent){
dojo.stopEvent(e);
if(this.queryCommandEnabled((e.shiftKey?"outdent":"indent"))){
this.execCommand((e.shiftKey?"outdent":"indent"));
}
}
if(dojo.isIE){
if(e.keyCode==dojo.keys.TAB&&!this.isTabIndent){
if(e.shiftKey&&!e.ctrlKey&&!e.altKey){
this.iframe.focus();
}else{
if(!e.shiftKey&&!e.ctrlKey&&!e.altKey){
this.tabStop.focus();
}
}
}else{
if(e.keyCode===dojo.keys.BACKSPACE&&this.document.selection.type==="Control"){
dojo.stopEvent(e);
this.execCommand("delete");
}else{
if((65<=e.keyCode&&e.keyCode<=90)||(e.keyCode>=37&&e.keyCode<=40)){
e.charCode=e.keyCode;
this.onKeyPress(e);
}
}
}
}
return true;
},onKeyUp:function(e){
return;
},setDisabled:function(_2b){
dojo.deprecated("dijit.Editor::setDisabled is deprecated","use dijit.Editor::attr(\"disabled\",boolean) instead",2);
this.attr("disabled",_2b);
},_setValueAttr:function(_2c){
this.setValue(_2c);
},_setDisableSpellCheckAttr:function(_2d){
if(this.document){
dojo.attr(this.document.body,"spellcheck",!_2d);
}else{
this.onLoadDeferred.addCallback(dojo.hitch(this,function(){
dojo.attr(this.document.body,"spellcheck",!_2d);
}));
}
this.disableSpellCheck=_2d;
},onKeyPress:function(e){
var c=(e.keyChar&&e.keyChar.toLowerCase())||e.keyCode,_2e=this._keyHandlers[c],_2f=arguments;
if(_2e&&!e.altKey){
dojo.some(_2e,function(h){
if(!(h.shift^e.shiftKey)&&!(h.ctrl^e.ctrlKey)){
if(!h.handler.apply(this,_2f)){
e.preventDefault();
}
return true;
}
},this);
}
if(!this._onKeyHitch){
this._onKeyHitch=dojo.hitch(this,"onKeyPressed");
}
setTimeout(this._onKeyHitch,1);
return true;
},addKeyHandler:function(key,_30,_31,_32){
if(!dojo.isArray(this._keyHandlers[key])){
this._keyHandlers[key]=[];
}
this._keyHandlers[key].push({shift:_31||false,ctrl:_30||false,handler:_32});
},onKeyPressed:function(){
this.onDisplayChanged();
},onClick:function(e){
this.onDisplayChanged(e);
},_onIEMouseDown:function(e){
if(!this._focused&&!this.disabled){
this.focus();
}
},_onBlur:function(e){
this.inherited(arguments);
var _33=this.getValue(true);
if(_33!=this.savedContent){
this.onChange(_33);
this.savedContent=_33;
}
},_onFocus:function(e){
if(!this.disabled){
if(!this._disabledOK){
this.attr("disabled",false);
}
this.inherited(arguments);
}
},blur:function(){
if(!dojo.isIE&&this.window.document.documentElement&&this.window.document.documentElement.focus){
this.window.document.documentElement.focus();
}else{
if(dojo.doc.body.focus){
dojo.doc.body.focus();
}
}
},focus:function(){
if(!dojo.isIE){
dijit.focus(this.iframe);
if(this._cursorToStart){
delete this._cursorToStart;
if(this.editNode.childNodes&&this.editNode.childNodes.length===1&&this.editNode.innerHTML==="&nbsp;"){
this.placeCursorAtStart();
}
}
}else{
if(this.editNode&&this.editNode.focus){
this.iframe.fireEvent("onfocus",document.createEventObject());
}
}
},updateInterval:200,_updateTimer:null,onDisplayChanged:function(e){
if(this._updateTimer){
clearTimeout(this._updateTimer);
}
if(!this._updateHandler){
this._updateHandler=dojo.hitch(this,"onNormalizedDisplayChanged");
}
this._updateTimer=setTimeout(this._updateHandler,this.updateInterval);
},onNormalizedDisplayChanged:function(){
delete this._updateTimer;
},onChange:function(_34){
},_normalizeCommand:function(cmd,_35){
var _36=cmd.toLowerCase();
if(_36=="formatblock"){
if(dojo.isSafari&&_35===undefined){
_36="heading";
}
}else{
if(_36=="hilitecolor"&&!dojo.isMoz){
_36="backcolor";
}
}
return _36;
},_qcaCache:{},queryCommandAvailable:function(_37){
var ca=this._qcaCache[_37];
if(ca!==undefined){
return ca;
}
return (this._qcaCache[_37]=this._queryCommandAvailable(_37));
},_queryCommandAvailable:function(_38){
var ie=1;
var _39=1<<1;
var _3a=1<<2;
var _3b=1<<3;
var _3c=1<<4;
function _3d(_3e){
return {ie:Boolean(_3e&ie),mozilla:Boolean(_3e&_39),webkit:Boolean(_3e&_3a),webkit420:Boolean(_3e&_3c),opera:Boolean(_3e&_3b)};
};
var _3f=null;
switch(_38.toLowerCase()){
case "bold":
case "italic":
case "underline":
case "subscript":
case "superscript":
case "fontname":
case "fontsize":
case "forecolor":
case "hilitecolor":
case "justifycenter":
case "justifyfull":
case "justifyleft":
case "justifyright":
case "delete":
case "selectall":
case "toggledir":
_3f=_3d(_39|ie|_3a|_3b);
break;
case "createlink":
case "unlink":
case "removeformat":
case "inserthorizontalrule":
case "insertimage":
case "insertorderedlist":
case "insertunorderedlist":
case "indent":
case "outdent":
case "formatblock":
case "inserthtml":
case "undo":
case "redo":
case "strikethrough":
case "tabindent":
_3f=_3d(_39|ie|_3b|_3c);
break;
case "blockdirltr":
case "blockdirrtl":
case "dirltr":
case "dirrtl":
case "inlinedirltr":
case "inlinedirrtl":
_3f=_3d(ie);
break;
case "cut":
case "copy":
case "paste":
_3f=_3d(ie|_39|_3c);
break;
case "inserttable":
_3f=_3d(_39|ie);
break;
case "insertcell":
case "insertcol":
case "insertrow":
case "deletecells":
case "deletecols":
case "deleterows":
case "mergecells":
case "splitcell":
_3f=_3d(ie|_39);
break;
default:
return false;
}
return (dojo.isIE&&_3f.ie)||(dojo.isMoz&&_3f.mozilla)||(dojo.isWebKit&&_3f.webkit)||(dojo.isWebKit>420&&_3f.webkit420)||(dojo.isOpera&&_3f.opera);
},execCommand:function(_40,_41){
var _42;
this.focus();
_40=this._normalizeCommand(_40,_41);
if(_41!==undefined){
if(_40=="heading"){
throw new Error("unimplemented");
}else{
if((_40=="formatblock")&&dojo.isIE){
_41="<"+_41+">";
}
}
}
var _43="_"+_40+"Impl";
if(this[_43]){
_42=this[_43](_41);
}else{
_41=arguments.length>1?_41:null;
if(_41||_40!="createlink"){
_42=this.document.execCommand(_40,false,_41);
}
}
this.onDisplayChanged();
return _42;
},queryCommandEnabled:function(_44){
if(this.disabled||!this._disabledOK){
return false;
}
_44=this._normalizeCommand(_44);
if(dojo.isMoz||dojo.isWebKit){
if(_44=="unlink"){
return this._sCall("hasAncestorElement",["a"]);
}else{
if(_44=="inserttable"){
return true;
}
}
}
if(dojo.isWebKit){
if(_44=="copy"){
_44="cut";
}else{
if(_44=="paste"){
return true;
}
}
}
var _45=dojo.isIE?this.document.selection.createRange():this.document;
try{
return _45.queryCommandEnabled(_44);
}
catch(e){
return false;
}
},queryCommandState:function(_46){
if(this.disabled||!this._disabledOK){
return false;
}
_46=this._normalizeCommand(_46);
try{
return this.document.queryCommandState(_46);
}
catch(e){
return false;
}
},queryCommandValue:function(_47){
if(this.disabled||!this._disabledOK){
return false;
}
var r;
_47=this._normalizeCommand(_47);
if(dojo.isIE&&_47=="formatblock"){
r=this._native2LocalFormatNames[this.document.queryCommandValue(_47)];
}else{
if(dojo.isMoz&&_47==="hilitecolor"){
var _48;
try{
_48=this.document.queryCommandValue("styleWithCSS");
}
catch(e){
_48=false;
}
this.document.execCommand("styleWithCSS",false,true);
r=this.document.queryCommandValue(_47);
this.document.execCommand("styleWithCSS",false,_48);
}else{
r=this.document.queryCommandValue(_47);
}
}
return r;
},_sCall:function(_49,_4a){
return dojo.withGlobal(this.window,_49,dijit._editor.selection,_4a);
},placeCursorAtStart:function(){
this.focus();
var _4b=false;
if(dojo.isMoz){
var _4c=this.editNode.firstChild;
while(_4c){
if(_4c.nodeType==3){
if(_4c.nodeValue.replace(/^\s+|\s+$/g,"").length>0){
_4b=true;
this._sCall("selectElement",[_4c]);
break;
}
}else{
if(_4c.nodeType==1){
_4b=true;
var tg=_4c.tagName?_4c.tagName.toLowerCase():"";
if(/br|input|img|base|meta|area|basefont|hr|link/.test(tg)){
this._sCall("selectElement",[_4c]);
}else{
this._sCall("selectElementChildren",[_4c]);
}
break;
}
}
_4c=_4c.nextSibling;
}
}else{
_4b=true;
this._sCall("selectElementChildren",[this.editNode]);
}
if(_4b){
this._sCall("collapse",[true]);
}
},placeCursorAtEnd:function(){
this.focus();
var _4d=false;
if(dojo.isMoz){
var _4e=this.editNode.lastChild;
while(_4e){
if(_4e.nodeType==3){
if(_4e.nodeValue.replace(/^\s+|\s+$/g,"").length>0){
_4d=true;
this._sCall("selectElement",[_4e]);
break;
}
}else{
if(_4e.nodeType==1){
_4d=true;
if(_4e.lastChild){
this._sCall("selectElement",[_4e.lastChild]);
}else{
this._sCall("selectElement",[_4e]);
}
break;
}
}
_4e=_4e.previousSibling;
}
}else{
_4d=true;
this._sCall("selectElementChildren",[this.editNode]);
}
if(_4d){
this._sCall("collapse",[false]);
}
},getValue:function(_4f){
if(this.textarea){
if(this.isClosed||!this.isLoaded){
return this.textarea.value;
}
}
return this._postFilterContent(null,_4f);
},_getValueAttr:function(){
return this.getValue(true);
},setValue:function(_50){
if(!this.isLoaded){
this.onLoadDeferred.addCallback(dojo.hitch(this,function(){
this.setValue(_50);
}));
return;
}
if(this.textarea&&(this.isClosed||!this.isLoaded)){
this.textarea.value=_50;
}else{
_50=this._preFilterContent(_50);
var _51=this.isClosed?this.domNode:this.editNode;
if(!_50&&dojo.isWebKit){
this._cursorToStart=true;
_50="&nbsp;";
}
_51.innerHTML=_50;
this._preDomFilterContent(_51);
}
this.onDisplayChanged();
},replaceValue:function(_52){
if(this.isClosed){
this.setValue(_52);
}else{
if(this.window&&this.window.getSelection&&!dojo.isMoz){
this.setValue(_52);
}else{
if(this.window&&this.window.getSelection){
_52=this._preFilterContent(_52);
this.execCommand("selectall");
if(!_52){
this._cursorToStart=true;
_52="&nbsp;";
}
this.execCommand("inserthtml",_52);
this._preDomFilterContent(this.editNode);
}else{
if(this.document&&this.document.selection){
this.setValue(_52);
}
}
}
}
},_preFilterContent:function(_53){
var ec=_53;
dojo.forEach(this.contentPreFilters,function(ef){
if(ef){
ec=ef(ec);
}
});
return ec;
},_preDomFilterContent:function(dom){
dom=dom||this.editNode;
dojo.forEach(this.contentDomPreFilters,function(ef){
if(ef&&dojo.isFunction(ef)){
ef(dom);
}
},this);
},_postFilterContent:function(dom,_54){
var ec;
if(!dojo.isString(dom)){
dom=dom||this.editNode;
if(this.contentDomPostFilters.length){
if(_54){
dom=dojo.clone(dom);
}
dojo.forEach(this.contentDomPostFilters,function(ef){
dom=ef(dom);
});
}
ec=dijit._editor.getChildrenHtml(dom);
}else{
ec=dom;
}
if(!dojo.trim(ec.replace(/^\xA0\xA0*/,"").replace(/\xA0\xA0*$/,"")).length){
ec="";
}
dojo.forEach(this.contentPostFilters,function(ef){
ec=ef(ec);
});
return ec;
},_saveContent:function(e){
var _55=dojo.byId(dijit._scopeName+"._editor.RichText.savedContent");
if(_55.value){
_55.value+=this._SEPARATOR;
}
_55.value+=this.name+":"+this.getValue(true);
},escapeXml:function(str,_56){
str=str.replace(/&/gm,"&amp;").replace(/</gm,"&lt;").replace(/>/gm,"&gt;").replace(/"/gm,"&quot;");
if(!_56){
str=str.replace(/'/gm,"&#39;");
}
return str;
},getNodeHtml:function(_57){
dojo.deprecated("dijit.Editor::getNodeHtml is deprecated","use dijit._editor.getNodeHtml instead",2);
return dijit._editor.getNodeHtml(_57);
},getNodeChildrenHtml:function(dom){
dojo.deprecated("dijit.Editor::getNodeChildrenHtml is deprecated","use dijit._editor.getChildrenHtml instead",2);
return dijit._editor.getChildrenHtml(dom);
},close:function(_58){
if(this.isClosed){
return false;
}
if(!arguments.length){
_58=true;
}
this._content=this.getValue();
var _59=(this.savedContent!=this._content);
if(this.interval){
clearInterval(this.interval);
}
if(this._webkitListener){
this.disconnect(this._webkitListener);
delete this._webkitListener;
}
if(dojo.isIE){
this.iframe.onfocus=null;
}
this.iframe._loadFunc=null;
if(this._iframeRegHandle){
dijit.unregisterIframe(this._iframeRegHandle);
delete this._iframeRegHandle;
}
if(this.textarea){
var s=this.textarea.style;
s.position="";
s.left=s.top="";
if(dojo.isIE){
s.overflow=this.__overflow;
this.__overflow=null;
}
this.textarea.value=_58?this._content:this.savedContent;
dojo.destroy(this.domNode);
this.domNode=this.textarea;
}else{
this.domNode.innerHTML=_58?this._content:this.savedContent;
}
delete this.iframe;
dojo.removeClass(this.domNode,"RichTextEditable");
this.isClosed=true;
this.isLoaded=false;
delete this.editNode;
delete this.focusNode;
if(this.window&&this.window._frameElement){
this.window._frameElement=null;
}
this.window=null;
this.document=null;
this.editingArea=null;
this.editorObject=null;
return _59;
},destroy:function(){
if(!this.isClosed){
this.close(false);
}
this.inherited(arguments);
},_removeMozBogus:function(_5a){
return _5a.replace(/\stype="_moz"/gi,"").replace(/\s_moz_dirty=""/gi,"").replace(/_moz_resizing="(true|false)"/gi,"");
},_removeWebkitBogus:function(_5b){
_5b=_5b.replace(/\sclass="webkit-block-placeholder"/gi,"");
_5b=_5b.replace(/\sclass="apple-style-span"/gi,"");
return _5b;
},_normalizeFontStyle:function(_5c){
return _5c.replace(/<(\/)?strong([ \>])/gi,"<$1b$2").replace(/<(\/)?em([ \>])/gi,"<$1i$2");
},_preFixUrlAttributes:function(_5d){
return _5d.replace(/(?:(<a(?=\s).*?\shref=)("|')(.*?)\2)|(?:(<a\s.*?href=)([^"'][^ >]+))/gi,"$1$4$2$3$5$2 _djrealurl=$2$3$5$2").replace(/(?:(<img(?=\s).*?\ssrc=)("|')(.*?)\2)|(?:(<img\s.*?src=)([^"'][^ >]+))/gi,"$1$4$2$3$5$2 _djrealurl=$2$3$5$2");
},_inserthorizontalruleImpl:function(_5e){
if(dojo.isIE){
return this._inserthtmlImpl("<hr>");
}
return this.document.execCommand("inserthorizontalrule",false,_5e);
},_unlinkImpl:function(_5f){
if((this.queryCommandEnabled("unlink"))&&(dojo.isMoz||dojo.isWebKit)){
var a=this._sCall("getAncestorElement",["a"]);
this._sCall("selectElement",[a]);
return this.document.execCommand("unlink",false,null);
}
return this.document.execCommand("unlink",false,_5f);
},_hilitecolorImpl:function(_60){
var _61;
if(dojo.isMoz){
this.document.execCommand("styleWithCSS",false,true);
_61=this.document.execCommand("hilitecolor",false,_60);
this.document.execCommand("styleWithCSS",false,false);
}else{
_61=this.document.execCommand("hilitecolor",false,_60);
}
return _61;
},_backcolorImpl:function(_62){
if(dojo.isIE){
_62=_62?_62:null;
}
return this.document.execCommand("backcolor",false,_62);
},_forecolorImpl:function(_63){
if(dojo.isIE){
_63=_63?_63:null;
}
return this.document.execCommand("forecolor",false,_63);
},_inserthtmlImpl:function(_64){
_64=this._preFilterContent(_64);
var rv=true;
if(dojo.isIE){
var _65=this.document.selection.createRange();
if(this.document.selection.type.toUpperCase()=="CONTROL"){
var n=_65.item(0);
while(_65.length){
_65.remove(_65.item(0));
}
n.outerHTML=_64;
}else{
_65.pasteHTML(_64);
}
_65.select();
}else{
if(dojo.isMoz&&!_64.length){
this._sCall("remove");
}else{
rv=this.document.execCommand("inserthtml",false,_64);
}
}
return rv;
},_boldImpl:function(_66){
if(dojo.isIE){
this._adaptIESelection();
}
return this.document.execCommand("bold",false,_66);
},_italicImpl:function(_67){
if(dojo.isIE){
this._adaptIESelection();
}
return this.document.execCommand("italic",false,_67);
},_underlineImpl:function(_68){
if(dojo.isIE){
this._adaptIESelection();
}
return this.document.execCommand("underline",false,_68);
},_strikethroughImpl:function(_69){
if(dojo.isIE){
this._adaptIESelection();
}
return this.document.execCommand("strikethrough",false,_69);
},_isNodeEmpty:function(_6a,_6b){
if(_6a.nodeType==1){
if(_6a.childNodes.length>0){
return this._isNodeEmpty(_6a.childNodes[0],_6b);
}
return true;
}else{
if(_6a.nodeType==3){
return (_6a.nodeValue.substring(_6b)=="");
}
}
return false;
},_removeStartingRangeFromRange:function(_6c,_6d){
if(_6c.nextSibling){
_6d.setStart(_6c.nextSibling,0);
}else{
var _6e=_6c.parentNode;
while(_6e&&_6e.nextSibling==null){
_6e=_6e.parentNode;
}
if(_6e){
_6d.setStart(_6e.nextSibling,0);
}
}
return _6d;
},_adaptIESelection:function(){
var _6f=dijit.range.getSelection(this.window);
if(_6f&&_6f.rangeCount&&!_6f.isCollapsed){
var _70=_6f.getRangeAt(0);
var _71=_70.startContainer;
var _72=_70.startOffset;
while(_71.nodeType==3&&_72>=_71.length&&_71.nextSibling){
_72=_72-_71.length;
_71=_71.nextSibling;
}
var _73=null;
while(this._isNodeEmpty(_71,_72)&&_71!=_73){
_73=_71;
_70=this._removeStartingRangeFromRange(_71,_70);
_71=_70.startContainer;
_72=0;
}
_6f.removeAllRanges();
_6f.addRange(_70);
}
}});
}
