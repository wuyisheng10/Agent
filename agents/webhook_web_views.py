def register_web_view_routes(app, render_dashboard_html_v2):
    @app.route("/web")
    def web_dashboard():
        return render_dashboard_html_v2(), 200, {"Content-Type": "text/html; charset=utf-8"}


def render_dashboard_html_v2() -> str:
    return """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>Yisheng 助理</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --blue:#007AFF;--blue-lt:#E3F0FF;--green:#34C759;--green-lt:#E6F9ED;
  --red:#FF3B30;--gray:#8E8E93;--bg:#F2F2F7;--surface:#FFF;
  --border:#D1D1D6;--text:#1C1C1E;--text2:#6C6C70;--radius:12px;
  --sidebar:270px;--hdr:52px;
}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  background:var(--bg);color:var(--text);height:100dvh;display:flex;flex-direction:column;overflow:hidden}
#hdr{height:var(--hdr);background:var(--surface);border-bottom:1px solid var(--border);
  display:flex;align-items:center;gap:10px;padding:0 16px;
  box-shadow:0 1px 3px rgba(0,0,0,.07);flex-shrink:0;z-index:50}
#hdr h1{font-size:16px;font-weight:700;flex:1}
.hbtn{font-size:12px;color:var(--blue);background:var(--blue-lt);
  border:none;border-radius:8px;padding:5px 10px;cursor:pointer;text-decoration:none}
#dot{width:9px;height:9px;border-radius:50%;background:var(--green);
  box-shadow:0 0 0 3px var(--green-lt);transition:all .3s;flex-shrink:0}
#dot.busy{background:#FF9500;box-shadow:0 0 0 3px #FFF3E0}
#body{flex:1;display:flex;overflow:hidden}
#sidebar{width:var(--sidebar);background:var(--surface);
  border-right:1px solid var(--border);overflow-y:auto;flex-shrink:0}
.sg{border-bottom:1px solid var(--border)}
.sghdr{display:flex;align-items:center;justify-content:space-between;
  padding:10px 14px;cursor:pointer;font-size:11px;font-weight:700;
  color:var(--text2);text-transform:uppercase;letter-spacing:.4px;
  background:#FAFAFA;user-select:none}
.sghdr:hover,.sghdr.open{background:var(--blue-lt);color:var(--blue)}
.sghdr .arr{font-size:10px;transition:transform .2s}
.sghdr.open .arr{transform:rotate(90deg)}
.sgitems{display:none;padding:3px 0}
.sgitems.open{display:block}
.sbtn{width:100%;text-align:left;border:none;background:transparent;
  padding:9px 16px 9px 20px;font-size:13px;color:var(--text);cursor:pointer;
  display:flex;align-items:center;justify-content:space-between;
  transition:background .12s;gap:6px}
.sbtn:hover{background:var(--blue-lt);color:var(--blue)}
.sbtn.direct .lbl{color:var(--blue);font-weight:500}
.sbtn .tag{font-size:10px;background:var(--blue);color:#fff;border-radius:4px;
  padding:1px 6px;flex-shrink:0}
.sbtn.form-btn .tag{background:var(--gray)}
#main{flex:1;display:flex;flex-direction:column;overflow:hidden}
#chat{flex:1;overflow-y:auto;padding:14px 10px;
  display:flex;flex-direction:column;gap:8px}
.msg{display:flex;max-width:88%;animation:fi .2s ease}
.msg.u{align-self:flex-end;flex-direction:row-reverse}
.msg.b{align-self:flex-start}
.bbl{padding:9px 13px;border-radius:16px;font-size:14px;
  line-height:1.6;white-space:pre-wrap;word-break:break-word}
.msg.u .bbl{background:var(--blue);color:#fff;border-bottom-right-radius:3px}
.msg.b .bbl{background:var(--blue-lt);color:var(--text);border-bottom-left-radius:3px}
.mt{font-size:10px;color:var(--text2);margin:3px 5px;align-self:flex-end}
.smsg .bbl{background:var(--bg);border:1px solid var(--border);
  display:flex;align-items:center;gap:7px}
.spin{width:15px;height:15px;border:2px solid var(--border);
  border-top-color:var(--blue);border-radius:50%;animation:sp .7s linear infinite;flex-shrink:0}
#pend{background:var(--surface);border-top:2px solid var(--blue);
  padding:10px 12px;display:none}
#pend.on{display:block}
#pendtitle{font-size:12px;font-weight:700;color:var(--blue);margin-bottom:8px}
#pendbtns{display:flex;flex-wrap:wrap;gap:6px}
.pbtn{background:var(--blue);color:#fff;border:none;border-radius:8px;
  padding:7px 11px;font-size:12px;cursor:pointer}
.pbtn:hover{opacity:.85}
.pbtn.cancel{background:var(--gray)}
#bar{background:var(--surface);border-top:1px solid var(--border);
  padding:8px 10px;display:flex;gap:7px;align-items:center;flex-shrink:0}
#upld{border:1.5px solid var(--border);border-radius:50%;width:38px;height:38px;
  font-size:16px;cursor:pointer;display:flex;align-items:center;justify-content:center;
  background:var(--bg);color:var(--text2);flex-shrink:0}
#upld:hover{background:var(--blue-lt);border-color:var(--blue);color:var(--blue)}
#finput{display:none}
#inp{flex:1;border:1.5px solid var(--border);border-radius:10px;
  padding:8px 12px;font-size:14px;background:var(--bg);
  outline:none;font-family:inherit;transition:border-color .2s}
#inp:focus{border-color:var(--blue)}
#sendbtn{background:var(--blue);color:#fff;border:none;border-radius:50%;
  width:38px;height:38px;font-size:16px;cursor:pointer;flex-shrink:0;
  display:flex;align-items:center;justify-content:center}
#sendbtn:disabled{opacity:.35;cursor:default}
#overlay{position:fixed;inset:0;background:rgba(0,0,0,.5);
  z-index:200;display:none;align-items:flex-end;justify-content:center;padding:0}
#overlay.on{display:flex}
#mbox{background:var(--surface);border-radius:20px 20px 0 0;
  width:100%;max-width:520px;max-height:90dvh;overflow-y:auto;
  box-shadow:0 -4px 30px rgba(0,0,0,.2);animation:su .25s ease}
#mtitle{font-size:15px;font-weight:700;padding:18px 18px 10px;
  display:flex;align-items:center;justify-content:space-between}
#mtitle button{border:none;background:var(--bg);border-radius:50%;
  width:28px;height:28px;font-size:14px;cursor:pointer;color:var(--text2)}
#mfields{padding:6px 18px 8px;display:flex;flex-direction:column;gap:12px}
.mf label{display:block;font-size:12px;font-weight:600;color:var(--text2);margin-bottom:4px}
.mf input,.mf select,.mf textarea{
  width:100%;border:1.5px solid var(--border);border-radius:10px;
  padding:9px 12px;font-size:14px;outline:none;font-family:inherit;
  transition:border-color .2s;background:var(--bg)}
.mf input:focus,.mf select:focus,.mf textarea:focus{border-color:var(--blue)}
.mf textarea{resize:vertical;min-height:70px}
.mf input.err,.mf select.err{border-color:var(--red)!important}
#macts{display:flex;gap:8px;padding:12px 18px 20px}
#mcancel{flex:1;padding:12px;border:1.5px solid var(--border);border-radius:10px;
  background:transparent;font-size:14px;cursor:pointer;font-family:inherit}
#mok{flex:2;padding:12px;background:var(--blue);color:#fff;
  border:none;border-radius:10px;font-size:14px;font-weight:600;cursor:pointer;font-family:inherit}
#fab{display:none;position:fixed;bottom:72px;right:16px;z-index:100;
  width:54px;height:54px;border-radius:50%;background:var(--blue);color:#fff;
  border:none;font-size:24px;box-shadow:0 4px 16px rgba(0,0,0,.25);cursor:pointer;
  align-items:center;justify-content:center}
#mobmenu{position:fixed;inset:0;z-index:150;display:none;flex-direction:column}
#mobmenu.on{display:flex}
#mobbg{flex:0 0 80px;background:rgba(0,0,0,.45)}
#mobsheet{flex:1;background:var(--surface);overflow-y:auto;
  border-radius:20px 20px 0 0;padding-bottom:env(safe-area-inset-bottom,16px)}
#mobclose{width:100%;padding:14px;border:none;background:transparent;
  font-size:13px;color:var(--text2);cursor:pointer;border-bottom:1px solid var(--border)}
.mgg{border-bottom:1px solid var(--border)}
.mgghdr{font-size:11px;font-weight:700;color:var(--text2);text-transform:uppercase;
  letter-spacing:.4px;padding:12px 18px 4px}
.mgbtn{width:100%;text-align:left;border:none;background:transparent;
  padding:12px 18px;font-size:14px;cursor:pointer;display:flex;align-items:center;
  justify-content:space-between;border-bottom:1px solid #F2F2F7}
.mgbtn:active,.mgbtn:hover{background:var(--blue-lt)}
.mgbtn.direct .lbl{color:var(--blue);font-weight:500}
.mgbtn .mtag{font-size:11px;color:var(--text2)}
@keyframes fi{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}
@keyframes su{from{opacity:0;transform:translateY(40px)}to{opacity:1;transform:none}}
@keyframes sp{to{transform:rotate(360deg)}}
@media(max-width:639px){#sidebar{display:none}#fab{display:flex}}
@media(min-width:640px){#fab,#mobmenu{display:none!important}}
</style>
</head>
<body>
<div id="hdr">
  <h1>🤖 Yisheng 助理</h1>
  <div id="dot"></div>
  <a href="/archive" class="hbtn" target="_blank">📁 歸檔瀏覽器</a>
</div>
<div id="body">
  <div id="sidebar"></div>
  <div id="main">
    <div id="chat"></div>
    <div id="pend"><div id="pendtitle">📋 待歸檔選項</div><div id="pendbtns"></div></div>
    <div id="bar">
      <input type="file" id="finput" accept="*/*">
      <button id="upld" title="上傳檔案" onclick="document.getElementById('finput').click()">📎</button>
      <input id="inp" type="text" placeholder="或直接輸入指令…" onkeydown="if(event.key==='Enter')doSend()">
      <button id="sendbtn" onclick="doSend()">➤</button>
    </div>
  </div>
</div>
<div id="overlay" onclick="if(event.target===this)closeModal()">
  <div id="mbox">
    <div id="mtitle"><span id="mtitletext"></span><button onclick="closeModal()">✕</button></div>
    <div id="mfields"></div>
    <div id="macts">
      <button id="mcancel" onclick="closeModal()">取消</button>
      <button id="mok" onclick="submitModal()">執行 ➤</button>
    </div>
  </div>
</div>
<button id="fab" onclick="openMob()">☰</button>
<div id="mobmenu">
  <div id="mobbg" onclick="closeMob()"></div>
  <div id="mobsheet">
    <button id="mobclose" onclick="closeMob()">✕ 關閉選單</button>
    <div id="mobcont"></div>
  </div>
</div>
<script>
const AMODES=["會議記錄","行事曆","夥伴跟進","市場開發","培訓資料","一般歸檔",
  "整理會議心得","歸檔會議紀錄","歸檔行動紀錄","歸檔文件","421故事歸檔","課程文宣歸檔"];
const GROUPS=[
  {label:"🎯 市場開發",items:[
    {label:"新增潛在家人",tag:"表單",form:{title:"新增潛在家人",
      fields:[{id:"n",lbl:"姓名",type:"text",req:1,ph:"例：張三"},
              {id:"j",lbl:"職業",type:"text",ph:"例：業務員"},
              {id:"c",lbl:"接觸管道",type:"text",ph:"例：朋友介紹"},
              {id:"r",lbl:"備註",type:"textarea",ph:"補充資訊"}],
      build:function(v){return "新增潛在家人 "+v.n+"|"+v.j+"|"+v.c+"|"+v.r;}}},
    {label:"查詢潛在家人",tag:"執行",cmd:"查詢潛在家人"},
    {label:"加入潛在家人資訊",tag:"表單",form:{title:"加入潛在家人資訊",
      fields:[{id:"n",lbl:"姓名",type:"text",req:1,ph:"請輸入潛在家人姓名"}],
      build:function(v){return "潛在家人資料 "+v.n;}}},
    {label:"修改潛在家人資訊",tag:"表單",form:{title:"修改潛在家人資訊",
      fields:[{id:"n",lbl:"姓名",type:"text",req:1,ph:"請輸入潛在家人姓名"},
              {id:"phone",lbl:"電話（選填）",type:"text",ph:"例：0912345678"},
              {id:"area",lbl:"地區（選填）",type:"text",ph:"例：台中西屯"},
              {id:"addr",lbl:"地址（選填）",type:"text",ph:"例：民生路123號"},
              {id:"status",lbl:"接觸狀態（選填）",type:"text",ph:"例：已聯繫"},
              {id:"next",lbl:"下次跟進日（選填）",type:"date"},
              {id:"product",lbl:"使用產品（選填）",type:"text",ph:"例：益生菌"},
              {id:"filter",lbl:"淨水器型號（選填）",type:"text",ph:"例：eSpring"},
              {id:"r",lbl:"備註（選填）",type:"textarea",ph:"補充資訊"}],
      build:function(v){
        var parts=["更新潛在家人 "+v.n];
        if(v.phone)parts.push("電話:"+v.phone);
        if(v.area)parts.push("地區:"+v.area);
        if(v.addr)parts.push("地址:"+v.addr);
        if(v.status)parts.push("接觸狀態:"+v.status);
        if(v.next)parts.push("下次跟進日:"+v.next);
        if(v.product)parts.push("使用產品:"+v.product);
        if(v.filter)parts.push("淨水器型號:"+v.filter);
        if(v.r)parts.push("備註:"+v.r);
        return parts.join("|");}}},
  ]},
  {label:"🎓 培訓系統",items:[
    {label:"新增培訓模組",tag:"表單",form:{title:"新增培訓模組",
      fields:[{id:"t",lbl:"模組名稱",type:"text",req:1,ph:"例：四個勇於"},
              {id:"c",lbl:"模組類型",type:"select",req:1,opts:["領導人特質","新人守則","帶線系統","市場實戰","畫畫培訓","產品培訓","事業培訓"]},
              {id:"g",lbl:"學習目標",type:"textarea",ph:"例：建立領導人思維與承擔能力"},
              {id:"s",lbl:"核心摘要",type:"textarea",ph:"例：勇於學習、勇於認錯、勇於改變、勇於承擔"}],
      build:function(v){return "新增培訓模組 "+v.t+" | "+v.c+" | "+v.g+" | "+v.s;}}},
    {label:"查詢培訓模組",tag:"表單",form:{title:"查詢培訓模組",
      fields:[{id:"t",lbl:"模組名稱（選填）",type:"text",ph:"空白則查全部"}],
      build:function(v){return v.t?"查詢培訓模組 "+v.t:"查詢培訓模組";}}},
    {label:"新增培訓課程",tag:"表單",form:{title:"新增培訓課程",
      fields:[{id:"t",lbl:"課程名稱",type:"text",req:1,ph:"例：領導人特質｜四個勇於"},
              {id:"m",lbl:"模組名稱",type:"text",req:1,ph:"請選擇模組"},
              {id:"d",lbl:"日期",type:"date",req:1},
              {id:"tm",lbl:"時間",type:"time",req:1},
              {id:"loc",lbl:"地點",type:"text",req:1,ph:"例：台南教室"},
              {id:"sp",lbl:"講師",type:"text",ph:"例：鐘老師"},
              {id:"aud",lbl:"對象",type:"select",req:1,opts:["潛在家人","夥伴","新手夥伴","核心夥伴"]}],
      build:function(v){return "新增培訓課程 "+v.t+" | "+v.m+" | "+v.d+" | "+v.tm+" | "+v.loc+" | "+v.sp+" | "+v.aud;}}},
    {label:"查詢培訓課程",tag:"表單",form:{title:"查詢培訓課程",
      fields:[{id:"d",lbl:"日期（選填）",type:"date"},
              {id:"m",lbl:"模組名稱（選填）",type:"text",ph:"空白則查全部"}],
      build:function(v){var q=v.d||v.m||"";return q?"查詢培訓課程 "+q:"查詢培訓課程";}}},
    {label:"新增培訓反思",tag:"表單",form:{title:"新增培訓反思",
      fields:[{id:"n",lbl:"夥伴姓名",type:"text",req:1,ph:"請選擇夥伴"},
              {id:"st",lbl:"課程名稱",type:"text",req:1,ph:"請選擇課程"},
              {id:"i",lbl:"悟到",type:"textarea",ph:"今天最大的提醒是什麼"},
              {id:"l",lbl:"學到",type:"textarea",ph:"學到哪個觀念或方法"},
              {id:"a",lbl:"做到",type:"textarea",ph:"接下來準備採取的行動"},
              {id:"g",lbl:"目標",type:"textarea",ph:"希望達成的具體目標"}],
      build:function(v){return "新增培訓反思 "+v.n+" | "+v.st+" | "+v.i+" | "+v.l+" | "+v.a+" | "+v.g;}}},
    {label:"查詢培訓進度",tag:"表單",form:{title:"查詢培訓進度",
      fields:[{id:"n",lbl:"夥伴姓名",type:"text",req:1,ph:"請選擇夥伴"}],
      build:function(v){return "查詢培訓進度 "+v.n;}}},
    {label:"查詢培訓總表",tag:"執行",cmd:"查詢培訓總表"},
    {label:"啟動七天法則",tag:"表單",form:{title:"啟動七天法則",
      fields:[{id:"n",lbl:"夥伴姓名",type:"text",req:1,ph:"請選擇夥伴"},
              {id:"d",lbl:"開始日期",type:"date",req:1},
              {id:"note",lbl:"教練備註（選填）",type:"textarea",ph:"例：先陪他完成七天暖身"}],
      build:function(v){return "啟動七天法則 "+v.n+" | "+v.d+" | "+v.note;}}},
    {label:"七天法則回報",tag:"表單",form:{title:"七天法則回報",
      fields:[{id:"n",lbl:"夥伴姓名",type:"text",req:1,ph:"請選擇夥伴"},
              {id:"day",lbl:"第幾天",type:"select",req:1,opts:["第1天","第2天","第3天","第4天","第5天","第6天","第7天"]},
              {id:"task",lbl:"任務內容",type:"textarea",req:1,ph:"例：聽 OPP、進教室、回報感想"},
              {id:"done",lbl:"完成狀態",type:"select",req:1,opts:["已完成","未完成"]},
              {id:"note",lbl:"備註（選填）",type:"textarea",ph:"例：今天對環境比較有感"}],
      build:function(v){return "七天法則回報 "+v.n+" | "+v.day+" | "+v.task+" | "+v.done+" | "+v.note;}}},
    {label:"查詢七天法則",tag:"表單",form:{title:"查詢七天法則",
      fields:[{id:"n",lbl:"夥伴姓名",type:"text",req:1,ph:"請選擇夥伴"}],
      build:function(v){return "查詢七天法則 "+v.n;}}},
    {label:"新增課後行動",tag:"表單",form:{title:"新增課後行動",
      fields:[{id:"n",lbl:"夥伴姓名",type:"text",req:1,ph:"請選擇夥伴"},
              {id:"st",lbl:"課程名稱",type:"text",req:1,ph:"請選擇課程"},
              {id:"content",lbl:"行動內容",type:"textarea",req:1,ph:"例：本週邀約 2 位新朋友"},
              {id:"due",lbl:"截止日期",type:"date",req:1}],
      build:function(v){return "新增課後行動 "+v.n+" | "+v.st+" | "+v.content+" | "+v.due;}}},
    {label:"回報課後行動",tag:"表單",form:{title:"回報課後行動",
      fields:[{id:"n",lbl:"夥伴姓名",type:"text",req:1,ph:"請選擇夥伴"},
              {id:"aid",lbl:"行動 ID",type:"text",req:1,ph:"先查詢課後行動取得 ID"},
              {id:"status",lbl:"狀態",type:"select",req:1,opts:["待執行","進行中","已完成","延後","需協助"]},
              {id:"note",lbl:"備註（選填）",type:"textarea",ph:"例：已完成第一步"}],
      build:function(v){return "回報課後行動 "+v.n+" | "+v.aid+" | "+v.status+" | "+v.note;}}},
    {label:"查詢課後行動",tag:"表單",form:{title:"查詢課後行動",
      fields:[{id:"n",lbl:"夥伴姓名",type:"text",req:1,ph:"請選擇夥伴"}],
      build:function(v){return "查詢課後行動 "+v.n;}}},
  ]},
      fields:[{id:"n",lbl:"夥伴姓名",type:"text",req:1,ph:"請選擇夥伴"},
              {id:"d",lbl:"開始日期",type:"date",req:1},
              {id:"note",lbl:"教練備註（選填）",type:"textarea",ph:"例：先陪他完成七天暖身"}],
      build:function(v){return "啟動七天法則 "+v.n+" | "+v.d+" | "+v.note;}}},
    {label:"七天法則回報",tag:"表單",form:{title:"七天法則回報",
      fields:[{id:"n",lbl:"夥伴姓名",type:"text",req:1,ph:"請選擇夥伴"},
              {id:"day",lbl:"第幾天",type:"select",req:1,opts:["第1天","第2天","第3天","第4天","第5天","第6天","第7天"]},
              {id:"task",lbl:"任務內容",type:"textarea",req:1,ph:"例：聽 OPP、進教室、回報感想"},
              {id:"done",lbl:"完成狀態",type:"select",req:1,opts:["已完成","未完成"]},
              {id:"note",lbl:"備註（選填）",type:"textarea",ph:"例：今天對環境比較有感"}],
      build:function(v){return "七天法則回報 "+v.n+" | "+v.day+" | "+v.task+" | "+v.done+" | "+v.note;}}},
    {label:"查詢七天法則",tag:"表單",form:{title:"查詢七天法則",
      fields:[{id:"n",lbl:"夥伴姓名",type:"text",req:1,ph:"請選擇夥伴"}],
      build:function(v){return "查詢七天法則 "+v.n;}}},
    {label:"新增課後行動",tag:"表單",form:{title:"新增課後行動",
      fields:[{id:"n",lbl:"夥伴姓名",type:"text",req:1,ph:"請選擇夥伴"},
              {id:"st",lbl:"課程名稱",type:"text",req:1,ph:"請選擇課程"},
              {id:"content",lbl:"行動內容",type:"textarea",req:1,ph:"例：本週邀約 2 位新朋友"},
              {id:"due",lbl:"截止日期",type:"date",req:1}],
      build:function(v){return "新增課後行動 "+v.n+" | "+v.st+" | "+v.content+" | "+v.due;}}},
    {label:"回報課後行動",tag:"表單",form:{title:"回報課後行動",
      fields:[{id:"n",lbl:"夥伴姓名",type:"text",req:1,ph:"請選擇夥伴"},
              {id:"aid",lbl:"行動 ID",type:"text",req:1,ph:"先查詢課後行動取得 ID"},
              {id:"status",lbl:"狀態",type:"select",req:1,opts:["待執行","進行中","已完成","延後","需協助"]},
              {id:"note",lbl:"備註（選填）",type:"textarea",ph:"例：已完成第一步"}],
      build:function(v){return "回報課後行動 "+v.n+" | "+v.aid+" | "+v.status+" | "+v.note;}}},
    {label:"查詢課後行動",tag:"表單",form:{title:"查詢課後行動",
      fields:[{id:"n",lbl:"夥伴姓名",type:"text",req:1,ph:"請選擇夥伴"}],
      build:function(v){return "查詢課後行動 "+v.n;}}},
  ]},
  {label:"🤝 夥伴陪伴",items:[
    {label:"跟進報告",tag:"執行",cmd:"跟進報告"},
    {label:"激勵夥伴",tag:"表單",form:{title:"激勵夥伴",
      fields:[{id:"n",lbl:"夥伴名稱",type:"text",req:1,ph:"例：建德"},
              {id:"s",lbl:"情境說明（選填）",type:"textarea",ph:"例：最近業績下滑"}],
      build:function(v){return "激勵 "+v.n+(v.s?" "+v.s:"");}}},
    {label:"里程碑記錄",tag:"表單",form:{title:"里程碑記錄",
      fields:[{id:"n",lbl:"夥伴名稱",type:"text",req:1,ph:"例：建德"},
              {id:"a",lbl:"成就描述",type:"textarea",ph:"例：首次達成業績目標"}],
      build:function(v){return "里程碑 "+v.n+(v.a?" "+v.a:"");}}},
    {label:"查詢所有夥伴",tag:"執行",cmd:"查詢夥伴"},
    {label:"查詢待跟進夥伴",tag:"執行",cmd:"查詢待跟進夥伴"},
    {label:"新增跟進夥伴",tag:"表單",form:{title:"新增跟進夥伴",
      fields:[{id:"n",lbl:"姓名",type:"text",req:1,ph:"姓名"},
              {id:"d",lbl:"下次跟進日期",type:"date",req:1},
              {id:"r",lbl:"備註",type:"textarea",ph:"例如 加入待跟進清單"}],
      build:function(v){return "新增跟進夥伴 "+v.n+" | "+v.d+" | "+v.r;}}},
    {label:"新增夥伴",tag:"表單",form:{title:"新增夥伴",
      fields:[{id:"n",lbl:"姓名",type:"text",req:1,ph:"姓名"},
              {id:"g",lbl:"目標",type:"text",ph:"例：月入三萬"},
              {id:"d",lbl:"下次跟進日期",type:"date"},
              {id:"r",lbl:"備註",type:"textarea",ph:"補充資訊"},
              {id:"c",lbl:"分類",type:"select",opts:["A","B","C"]}],
      build:function(v){return "新增夥伴 "+v.n+" | "+v.g+" | "+v.d+" | "+v.r+" | "+v.c;}}},
    {label:"更新夥伴",tag:"表單",form:{title:"更新夥伴",
      fields:[{id:"n",lbl:"姓名",type:"text",req:1,ph:"姓名"},
              {id:"l",lbl:"層級",type:"text",ph:"例：1"},
              {id:"s",lbl:"近況",type:"text",ph:"例：持續跟進"},
              {id:"d",lbl:"下次跟進日期",type:"date"},
              {id:"ci",lbl:"聯絡資訊",type:"text",ph:"例：LINE:abc123"},
              {id:"r",lbl:"備註",type:"textarea",ph:"補充資訊"},
              {id:"t",lbl:"類型",type:"text",ph:"例：直銷商"},
              {id:"no",lbl:"編號",type:"text",ph:"例：7519213"},
              {id:"p",lbl:"合夥人",type:"text",ph:"例：王小明"},
              {id:"sp",lbl:"推薦人",type:"text",ph:"例：陳薾云"},
              {id:"ed",lbl:"到期日",type:"date"},
              {id:"ym",lbl:"年月",type:"text",ph:"例：2026-03"},
              {id:"rt",lbl:"一年內新上獎銜",type:"text",ph:"例：翡翠"},
              {id:"fb",lbl:"首次獎金%",type:"text",ph:"例：3%"},
              {id:"cv",lbl:"現金抵用券",type:"text",ph:"例：有"},
              {id:"sp2",lbl:"購物積點",type:"text",ph:"例：2821"},
              {id:"cp",lbl:"優惠券",type:"text",ph:"例：有"},
              {id:"m1",lbl:"本月購貨",type:"text",ph:"例：V"},
              {id:"m2",lbl:"上月購貨",type:"text",ph:"例：V"},
              {id:"m3",lbl:"前2月購貨",type:"text",ph:"例：V"},
              {id:"m4",lbl:"前3月購貨",type:"text",ph:"例：V"},
              {id:"cg",lbl:"分類",type:"select",opts:["","A","B","C"]}],
      build:function(v){return "更新夥伴 "+v.n+" | "+v.l+" | "+v.s+" | "+v.d+" | "+v.ci+" | "+v.r+" | "+v.t+" | "+v.no+" | "+v.p+" | "+v.sp+" | "+v.ed+" | "+v.ym+" | "+v.rt+" | "+v.fb+" | "+v.cv+" | "+v.sp2+" | "+v.cp+" | "+v.m1+" | "+v.m2+" | "+v.m3+" | "+v.m4+" | "+v.cg;}}},
    {label:"查詢指定夥伴",tag:"表單",form:{title:"查詢指定夥伴",
      fields:[{id:"n",lbl:"姓名",type:"text",req:1,ph:"例：建德"}],
      build:function(v){return "查詢夥伴 "+v.n;}}},
    {label:"跟進夥伴",tag:"表單",form:{title:"跟進夥伴",
      fields:[{id:"n",lbl:"姓名",type:"text",req:1,ph:"姓名"},
              {id:"s",lbl:"狀態",type:"text",ph:"例：持續跟進"},
              {id:"d",lbl:"下次跟進日期",type:"date"},
              {id:"r",lbl:"備註",type:"textarea",ph:"補充資訊"}],
      build:function(v){return "跟進夥伴 "+v.n+" | "+v.s+" | "+v.d+" | "+v.r;}}},
    {label:"刪除夥伴",tag:"表單",form:{title:"刪除夥伴",
      fields:[{id:"n",lbl:"姓名",type:"text",req:1,ph:"例：建德"}],
      build:function(v){return "刪除夥伴 "+v.n;}}},
  ]},
  {label:"🗓️ 行事曆",items:[
    {label:"查詢今日行事曆",tag:"執行",cmd:"查詢行事曆"},
    {label:"查詢過往行事曆",tag:"執行",cmd:"查詢過往行事曆"},
    {label:"查詢全部行事曆",tag:"執行",cmd:"查詢全部行事曆"},
    {label:"上傳行事曆圖片",tag:"執行",cmd:"上傳行事曆圖片"},
    {label:"手動新增行事曆",tag:"表單",form:{title:"新增行事曆事件",
      fields:[{id:"d",lbl:"日期",type:"date",req:1},
              {id:"t",lbl:"時間（選填）",type:"time"},
              {id:"ti",lbl:"標題",type:"text",req:1,ph:"活動名稱"},
              {id:"r",lbl:"備註（選填）",type:"textarea",ph:"補充說明"}],
      build:function(v){return "新增行事曆 "+v.d+(v.t?" "+v.t:"")+" "+v.ti+(v.r?" | "+v.r:"");}}},
    {label:"修改行事曆",tag:"表單",form:{title:"修改行事曆事件",
      fields:[{id:"id",lbl:"事件 ID（EVT-XXXX）",type:"text",req:1,ph:"先查詢行事曆取得 ID"},
              {id:"d",lbl:"日期",type:"date",req:1},
              {id:"t",lbl:"時間（選填）",type:"time"},
              {id:"ti",lbl:"標題",type:"text",req:1,ph:"活動名稱"},
              {id:"r",lbl:"備註（選填）",type:"textarea",ph:"補充說明"}],
      build:function(v){return "修改行事曆 "+v.id+" "+v.d+(v.t?" "+v.t:"")+" "+v.ti+(v.r?" | "+v.r:"");}}},
    {label:"刪除行事曆",tag:"表單",form:{title:"刪除行事曆事件",
      fields:[{id:"id",lbl:"事件 ID（EVT-XXXX）",type:"text",req:1,ph:"先查詢行事曆取得 ID"}],
      build:function(v){return "刪除行事曆 "+v.id;}}},
  ]},
  {label:"📂 歸類模式",items:[
    {label:"查詢目前歸類模式",tag:"執行",cmd:"歸類模式"},
    {label:"設定歸類模式",tag:"表單",form:{title:"設定歸類模式",
      fields:[{id:"m",lbl:"歸類模式",type:"select",req:1,opts:AMODES},
              {id:"p",lbl:"人員名稱（選填）",type:"text",ph:"例：建德"},
              {id:"d",lbl:"日期（選填）",type:"date"}],
      build:function(v){var c="歸類模式";if(v.p)c+=" "+v.p;c+=" "+v.m;if(v.d)c+=" "+v.d;return c;}}},
    {label:"關閉歸類模式",tag:"執行",cmd:"關閉歸類模式"},
    {label:"查詢所有歸檔",tag:"執行",cmd:"查詢歸檔"},
    {label:"查詢指定人員歸檔",tag:"表單",form:{title:"查詢指定人員歸檔",
      fields:[{id:"n",lbl:"人員名稱",type:"text",req:1,ph:"例：建德"}],
      build:function(v){return "查詢歸檔 "+v.n;}}},
  ]},
  {label:"📖 培訓記錄",items:[
    {label:"整理今日培訓記錄",tag:"執行",cmd:"整理"},
    {label:"整理指定日期記錄",tag:"表單",form:{title:"整理指定日期記錄",
      fields:[{id:"d",lbl:"日期",type:"date",req:1}],
      build:function(v){return "整理 "+v.d.replace(/-/g,"");}}},
    {label:"再次整理（強制覆蓋）",tag:"執行",cmd:"再次整理"},
    {label:"查詢培訓記錄",tag:"表單",form:{title:"查詢指定日期培訓記錄",
      fields:[{id:"d",lbl:"日期",type:"date",req:1}],
      build:function(v){return "MTG-"+v.d.replace(/-/g,"");}}},
  ]},
  {label:"🛍️ 安麗產品歸檔",items:[
    {label:"💊 營養保健 (Nutrilite)",tag:"執行",cmd:"營養保健歸檔"},
    {label:"💄 美容保養 (Artistry)",tag:"執行",cmd:"美容保養歸檔"},
    {label:"🧹 居家清潔 (Home)",tag:"執行",cmd:"居家清潔歸檔"},
    {label:"🪥 個人護理 (Glister)",tag:"執行",cmd:"個人護理歸檔"},
    {label:"🍳 廚具與生活用品",tag:"執行",cmd:"廚具生活歸檔"},
    {label:"💧 空氣與水處理設備",tag:"執行",cmd:"空水設備歸檔"},
    {label:"⚖️ 體重管理與運動營養",tag:"執行",cmd:"體重管理歸檔"},
    {label:"🌸 香氛與個人風格",tag:"執行",cmd:"香氛風格歸檔"},
    {label:"🛠️ 事業工具與教育系統",tag:"執行",cmd:"事業工具歸檔"},
  ]},
  {label:"📝 故事分類",items:[
    {label:"👤 人物故事歸檔",tag:"表單",form:{title:"人物故事歸檔",
      fields:[{id:"n",lbl:"人物名稱",type:"text",req:1,ph:"例：建德",pick:"people"}],
      build:function(v){return "潛在家人資料 "+v.n;}}},
    {label:"📖 產品故事歸檔",tag:"執行",cmd:"產品故事歸檔"},
  ]},
  {label:"🎓 課程邀約",items:[
    {label:"查詢課程會議",tag:"執行",cmd:"查詢課程會議"},
    {label:"新增課程會議",tag:"表單",form:{title:"新增課程會議",
      fields:[{id:"d",lbl:"日期",type:"date",req:1},
              {id:"t",lbl:"時間（選填）",type:"time"},
              {id:"ti",lbl:"標題",type:"text",req:1,ph:"例：四月OPP說明會"},
              {id:"lo",lbl:"地點（選填）",type:"text",ph:"例：台中大里店"},
              {id:"r",lbl:"說明（選填）",type:"textarea",ph:"例：歡迎帶朋友"},
              {id:"sp",lbl:"演講貴賓（選填）",type:"text",ph:"例：鑽石李大明"},
              {id:"spb",lbl:"貴賓介紹（選填）",type:"textarea",ph:"例：20年資深鑽石，擅長事業說明與激勵"},
              {id:"tp",lbl:"課程主題（選填）",type:"text",ph:"例：事業機會介紹"},
              {id:"tpd",lbl:"主題介紹（選填）",type:"textarea",ph:"例：從零到鑽石的實戰分享，含產品體驗與收入模型"}],
      build:function(v){
        var s="新增課程會議 "+v.d+(v.t?" "+v.t:"")+" "+v.ti;
        var ext=[v.lo||"",v.r||"",v.sp||"",v.spb||"",v.tp||"",v.tpd||""];
        var last=-1;
        for(var i=ext.length-1;i>=0;i--){if(ext[i]){last=i;break;}}
        if(last>=0){for(var i=0;i<=last;i++)s+="|"+(ext[i]||"");}
        return s;}}},
    {label:"從行事曆加入課程",tag:"表單",form:{title:"從行事曆加入課程",
      fields:[{id:"k",lbl:"關鍵字（選填）",type:"text",ph:"例：OPP、培訓"}],
      build:function(v){return "從行事曆加入課程"+(v.k?" "+v.k:"");}}},
    {label:"修改課程會議",tag:"表單",form:{title:"修改課程會議",
      fields:[{id:"id",lbl:"課程 ID（COURSE-XXXX）",type:"text",req:1,ph:"先查詢課程會議取得 ID"},
              {id:"ti",lbl:"標題（選填）",type:"text",ph:"留空＝不修改"},
              {id:"d",lbl:"日期（選填）",type:"date"},
              {id:"t",lbl:"時間（選填）",type:"time"},
              {id:"lo",lbl:"地點（選填）",type:"text",ph:"留空＝不修改"},
              {id:"r",lbl:"說明（選填）",type:"textarea",ph:"留空＝不修改"},
              {id:"sp",lbl:"演講貴賓（選填）",type:"text",ph:"留空＝不修改"},
              {id:"spb",lbl:"貴賓介紹（選填）",type:"textarea",ph:"留空＝不修改"},
              {id:"tp",lbl:"課程主題（選填）",type:"text",ph:"留空＝不修改"},
              {id:"tpd",lbl:"主題介紹（選填）",type:"textarea",ph:"留空＝不修改"}],
      build:function(v){
        var MAP={ti:"標題",d:"日期",t:"時間",lo:"地點",r:"說明",sp:"演講貴賓",spb:"貴賓介紹",tp:"課程主題",tpd:"主題介紹"};
        var pairs=[];
        Object.keys(MAP).forEach(function(k){if(v[k])pairs.push(MAP[k]+":"+v[k]);});
        if(!pairs.length)return "修改課程會議 "+v.id+" 標題:（請填寫至少一個欄位）";
        return "修改課程會議 "+v.id+" "+pairs.join("|");}}},
    {label:"刪除課程會議",tag:"表單",form:{title:"刪除課程會議",
      fields:[{id:"id",lbl:"課程 ID（COURSE-XXXX）",type:"text",req:1,ph:"先查詢課程會議取得 ID"}],
      build:function(v){return "刪除課程會議 "+v.id;}}},
    {label:"查詢課程文宣",tag:"執行",cmd:"查詢課程文宣"},
    {label:"新增課程文宣",tag:"表單",form:{title:"新增課程文宣",
      fields:[{id:"ti",lbl:"標題",type:"text",req:1,ph:"例：四月OPP邀約文宣"},
              {id:"c",lbl:"內文",type:"textarea",req:1,ph:"輸入文宣內容"}],
      build:function(v){return "新增課程文宣 "+v.ti+"|"+v.c;}}},
    {label:"優化課程文宣（AI）",tag:"表單",form:{title:"優化課程文宣",
      fields:[{id:"id",lbl:"文宣 ID（PROMO-XXXX）",type:"text",req:1,ph:"先查詢課程文宣取得 ID",pick:"promo"}],
      build:function(v){return "優化課程文宣 "+v.id;}}},
    {label:"邀約文宣－潛在家人（AI）",tag:"執行",cmd:"邀約文宣 潛在家人"},
    {label:"邀約文宣－跟進夥伴（AI）",tag:"表單",form:{title:"跟進夥伴邀約文宣",
      fields:[{id:"n",lbl:"姓名（選填，空白＝通用）",type:"text",ph:"例：建德"}],
      build:function(v){return "邀約文宣 跟進夥伴"+(v.n?" "+v.n:"");}}},
    {label:"查詢已產生的邀約文宣",tag:"執行",cmd:"查詢已產生的今日之後會議邀約文宣"},
    {label:"修改已產生的邀約文宣",tag:"表單",form:{title:"修改已產生的邀約文宣",
      fields:[{id:"id",lbl:"課程 ID（COURSE-XXXX）",type:"text",req:1,ph:"先查詢已產生的邀約文宣取得 ID"},
              {id:"n",lbl:"姓名",type:"text",req:1,ph:"例：吳建德"},
              {id:"c",lbl:"新內容",type:"textarea",req:1,ph:"輸入修改後的邀約文宣"}],
      build:function(v){return "修改已產生的今日之後會議邀約文宣 "+v.id+" | "+v.n+" | "+v.c;}}},
  ]},
  {label:"📧 每日報告",items:[
    {label:"寄送每日報告",tag:"執行",cmd:"寄送每日報告"},
  ]},
  {label:"🥗 營養評估",items:[
    {label:"查詢營養素標準",tag:"表單",form:{title:"查詢營養素標準",
      fields:[{id:"g",lbl:"性別",type:"select",req:1,options:[{v:"男",l:"男"},{v:"女",l:"女"}]},
              {id:"a",lbl:"年齡",type:"text",req:1,ph:"例：30"},
              {id:"m",lbl:"餐別（可不填）",type:"select",req:0,options:[{v:"",l:"全日"},{v:"早餐",l:"早餐"},{v:"午餐",l:"午餐"},{v:"晚餐",l:"晚餐"}]}],
      build:function(v){var s="查詢營養素標準 "+v.g+" "+v.a;if(v.m)s+=" "+v.m;return s;}}},
    {label:"營養素運作原理",tag:"表單",form:{title:"查詢營養素運作原理",
      fields:[{id:"n",lbl:"營養素名稱",type:"text",req:1,ph:"例：鈣、維生素D、鐵"}],
      build:function(v){return "營養素運作原理 "+v.n;}}},
    {label:"列出所有營養素",tag:"執行",cmd:"列出營養素"},
    {label:"更新官方標準",tag:"執行",cmd:"下載營養素標準"},
    {label:"開始飲食評估",tag:"表單",form:{title:"開始飲食評估",
      fields:[{id:"g",lbl:"性別",type:"select",req:1,options:[{v:"男",l:"男"},{v:"女",l:"女"}]},
              {id:"a",lbl:"年齡",type:"text",req:1,ph:"例：30"},
              {id:"p",lbl:"歸檔對象姓名（可不填）",type:"text",req:0,ph:"例：王小明"}],
      build:function(v){var s="開始飲食評估 "+v.g+" "+v.a;if(v.p)s+=" 對象:"+v.p;return s;}}},
    {label:"設定歸檔對象",tag:"表單",form:{title:"設定歸檔對象",
      fields:[{id:"n",lbl:"姓名",type:"text",req:1,ph:"例：王小明"}],
      build:function(v){return "設定評估對象 "+v.n;}}},
    {label:"設定下一張餐別",tag:"表單",form:{title:"設定餐別",
      fields:[{id:"m",lbl:"餐別",type:"select",req:1,options:[{v:"早餐",l:"早餐"},{v:"午餐",l:"午餐"},{v:"晚餐",l:"晚餐"},{v:"宵夜",l:"宵夜"}]}],
      build:function(v){return "設定餐別 "+v.m;}}},
    {label:"執行飲食評估",tag:"表單",form:{title:"執行飲食評估（AI分析）",
      fields:[{id:"w",lbl:"今日飲水量 (ml)",type:"text",req:1,ph:"例：1500"}],
      build:function(v){return "評估飲食 喝水量"+v.w+"ml";}}},
    {label:"飲食評估狀態",tag:"執行",cmd:"飲食評估狀態"},
    {label:"清除飲食評估",tag:"執行",cmd:"清除飲食評估"},
  ]},
  {label:"❓ 說明",items:[
    {label:"顯示所有指令",tag:"執行",cmd:"指令集"},
  ]},
];
// Build sidebar
function buildSB(){
  var sb=document.getElementById("sidebar");sb.innerHTML="";
  GROUPS.forEach(function(g){
    var sec=document.createElement("div");sec.className="sg";
    var hdr=document.createElement("div");hdr.className="sghdr";
    hdr.innerHTML=g.label+' <span class="arr">▶</span>';
    var items=document.createElement("div");items.className="sgitems";
    hdr.onclick=function(){hdr.classList.toggle("open");items.classList.toggle("open");};
    g.items.forEach(function(item){
      var b=document.createElement("button");
      b.className="sbtn"+(item.cmd&&!item.form?" direct":"")+(item.form?" form-btn":"");
      b.innerHTML='<span class="lbl">'+item.label+'</span><span class="tag">'+item.tag+'</span>';
      b.onclick=function(){clickItem(item);};
      items.appendChild(b);
    });
    sec.appendChild(hdr);sec.appendChild(items);sb.appendChild(sec);
  });
}
buildSB();
// Build mobile menu
function buildMob(){
  var c=document.getElementById("mobcont");c.innerHTML="";
  GROUPS.forEach(function(g){
    var gh=document.createElement("div");gh.className="mgg";
    var ghl=document.createElement("div");ghl.className="mgghdr";ghl.textContent=g.label;
    gh.appendChild(ghl);
    g.items.forEach(function(item){
      var b=document.createElement("button");
      b.className="mgbtn"+(item.cmd&&!item.form?" direct":"");
      b.innerHTML='<span class="lbl">'+item.label+'</span><span class="mtag">'+item.tag+'</span>';
      b.onclick=function(){closeMob();clickItem(item);};
      gh.appendChild(b);
    });
    c.appendChild(gh);
  });
}
buildMob();
function openMob(){document.getElementById("mobmenu").classList.add("on");}
function closeMob(){document.getElementById("mobmenu").classList.remove("on");}
// Modal
var _build=null;
var _partnerCache=null;
var _prospectCache=null;
var _promoCache=null;
var _trainingModuleCache=null;
var _trainingSessionCache=null;
function _fieldIds(f){return (f.fields||[]).map(function(x){return x.id;});}
function _isUpdatePartnerForm(f){
  var ids=_fieldIds(f);
  return ids.includes("n")&&ids.includes("l")&&ids.includes("ci")&&ids.includes("cg");
}
function _isFollowupAddForm(f){
  var ids=_fieldIds(f);
  return ids.includes("n")&&ids.includes("d")&&ids.includes("r")&&!ids.includes("g")&&!ids.includes("s")&&!ids.includes("ci");
}
function _isFollowupForm(f){
  var ids=_fieldIds(f);
  return ids.includes("n")&&ids.includes("s")&&ids.includes("d")&&!ids.includes("ci");
}
function _isMotivateForm(f){
  var ids=_fieldIds(f);
  return ids.length===2&&ids.includes("n")&&ids.includes("s");
}
function _isTrainingProgressForm(f){
  return !!f && (f.title||"")==="查詢培訓進度";
}
function _isTrainingReflectionForm(f){
  return !!f && (f.title||"")==="新增培訓反思";
}
function _isTrainingSessionForm(f){
  return !!f && (f.title||"")==="新增培訓課程";
}
function _isTrainingSessionLookupForm(f){
  return !!f && (f.title||"")==="查詢培訓課程";
}
function _isTrainingModuleLookupForm(f){
  return !!f && (f.title||"")==="查詢培訓模組";
}
function _isSevenDayForm(f){
  return !!f && ((f.title||"")==="啟動七天法則"||(f.title||"")==="七天法則回報"||(f.title||"")==="查詢七天法則");
}
function _isTrainingActionForm(f){
  return !!f && ((f.title||"")==="新增課後行動"||(f.title||"")==="回報課後行動"||(f.title||"")==="查詢課後行動");
}
function _isMilestoneForm(f){
  return !!f && (f.title||"")==="里程碑記錄";
}
function _isPartnerLookupForm(f){
  return !!f && (f.title||"")==="查詢指定夥伴";
}
function _isStoryPersonForm(f){
  return !!f && (f.title||"")==="人物故事歸檔";
}
function _isPromoSelectForm(f){
  return !!f && (f.title||"")==="優化課程文宣";
}
async function _getPartners(){
  if(_partnerCache)return _partnerCache;
  var r=await fetch("/api/partners");
  var d=await r.json();
  _partnerCache=(d&&d.result)||[];
  return _partnerCache;
}
async function _getProspects(){
  if(_prospectCache)return _prospectCache;
  var r=await fetch("/api/prospects");
  var d=await r.json();
  _prospectCache=(d&&d.result)||[];
  return _prospectCache;
}
async function _getCoursePromos(){
  if(_promoCache)return _promoCache;
  var r=await fetch("/api/course-promos");
  var d=await r.json();
  _promoCache=(d&&d.result)||[];
  return _promoCache;
}
async function _getTrainingModules(){
  if(_trainingModuleCache)return _trainingModuleCache;
  var r=await fetch("/api/training-modules");
  var d=await r.json();
  _trainingModuleCache=(d&&d.result)||[];
  return _trainingModuleCache;
}
async function _getTrainingSessions(){
  if(_trainingSessionCache)return _trainingSessionCache;
  var r=await fetch("/api/training-sessions");
  var d=await r.json();
  _trainingSessionCache=(d&&d.result)||[];
  return _trainingSessionCache;
}
async function _getStoryPeople(){
  const [partners, prospects] = await Promise.all([_getPartners(), _getProspects()]);
  var seen={};
  var people=[];
  partners.forEach(function(p){
    var name=(p.name||"").trim();
    if(!name||seen[name])return;
    seen[name]=1;
    people.push({name:name, source:"夥伴", category:p.category||"", stage:p.stage||""});
  });
  prospects.forEach(function(p){
    var name=(p.name||"").trim();
    if(!name||seen[name])return;
    seen[name]=1;
    people.push({name:name, source:"潛在家人", category:p.category||"", stage:p.status||""});
  });
  people.sort(function(a,b){return a.name.localeCompare(b.name,"zh-Hant");});
  return people;
}
async function _hydratePartnerSelect(formDef){
  if(!_isUpdatePartnerForm(formDef)&&!_isFollowupAddForm(formDef)&&!_isFollowupForm(formDef)&&!_isMotivateForm(formDef)&&!_isTrainingProgressForm(formDef)&&!_isTrainingReflectionForm(formDef)&&!_isSevenDayForm(formDef)&&!_isTrainingActionForm(formDef)&&!_isMilestoneForm(formDef)&&!_isPartnerLookupForm(formDef))return;
  var el=document.getElementById("mf_n");
  if(!el)return;
  var partners=await _getPartners();
  if(_isFollowupAddForm(formDef)||_isFollowupForm(formDef)){
    partners=partners.filter(function(p){ return (p.stage||"")==="待跟進"; });
  } else if(_isMotivateForm(formDef)){
    partners=partners.filter(function(p){ return (p.stage||"").indexOf("激勵")!==-1; });
  }
  var cur=el.value||"";
  var sel=document.createElement("select");
  sel.id=el.id;
  sel.required=true;
  var first=document.createElement("option");
  first.value="";
  first.textContent="請選擇夥伴";
  sel.appendChild(first);
  partners.forEach(function(p){
    var o=document.createElement("option");
    o.value=p.name;
    var extra=[];
    if(p.level)extra.push("層級"+p.level);
    if(p.stage)extra.push(p.stage);
    if(p.category)extra.push("分類"+p.category);
    o.textContent=extra.length?(p.name+"｜"+extra.join("｜")):p.name;
    if(cur&&cur===p.name)o.selected=true;
    sel.appendChild(o);
  });
  el.replaceWith(sel);
  if(_isUpdatePartnerForm(formDef)){
    sel.addEventListener("change", function(){ _prefillPartnerForm(sel.value); });
    if(sel.value)_prefillPartnerForm(sel.value);
  }
}
async function _hydrateStoryPeopleSelect(formDef){
  if(!_isStoryPersonForm(formDef))return;
  var el=document.getElementById("mf_n");
  if(!el)return;
  var people=await _getStoryPeople();
  var cur=el.value||"";
  var sel=document.createElement("select");
  sel.id=el.id;
  sel.required=true;
  var first=document.createElement("option");
  first.value="";
  first.textContent="請選擇人物";
  sel.appendChild(first);
  people.forEach(function(p){
    var o=document.createElement("option");
    o.value=p.name;
    var extra=[];
    if(p.source)extra.push(p.source);
    if(p.category)extra.push("分類"+p.category);
    if(p.stage)extra.push(p.stage);
    o.textContent=extra.length?(p.name+"｜"+extra.join("｜")):p.name;
    if(cur&&cur===p.name)o.selected=true;
    sel.appendChild(o);
  });
  el.replaceWith(sel);
}
async function _hydrateTrainingModuleSelect(formDef){
  if(!_isTrainingSessionForm(formDef)&&!_isTrainingSessionLookupForm(formDef)&&!_isTrainingModuleLookupForm(formDef))return;
  var modules=await _getTrainingModules();
  if(_isTrainingSessionForm(formDef)||_isTrainingSessionLookupForm(formDef)){
    var el=document.getElementById("mf_m");
    if(el){
      var cur=el.value||"";
      var sel=document.createElement("select");
      sel.id=el.id;
      if(_isTrainingSessionForm(formDef))sel.required=true;
      var first=document.createElement("option");
      first.value="";
      first.textContent=_isTrainingSessionForm(formDef)?"請選擇模組":"（全部模組）";
      sel.appendChild(first);
      modules.forEach(function(m){
        var o=document.createElement("option");
        o.value=m.title;
        o.textContent=m.category?(m.title+"｜"+m.category):m.title;
        if(cur&&cur===m.title)o.selected=true;
        sel.appendChild(o);
      });
      el.replaceWith(sel);
    }
  }
  if(_isTrainingModuleLookupForm(formDef)){
    var tel=document.getElementById("mf_t");
    if(tel){
      var cur2=tel.value||"";
      var sel2=document.createElement("select");
      sel2.id=tel.id;
      var first2=document.createElement("option");
      first2.value="";
      first2.textContent="（全部模組）";
      sel2.appendChild(first2);
      modules.forEach(function(m){
        var o2=document.createElement("option");
        o2.value=m.title;
        o2.textContent=m.category?(m.title+"｜"+m.category):m.title;
        if(cur2&&cur2===m.title)o2.selected=true;
        sel2.appendChild(o2);
      });
      tel.replaceWith(sel2);
    }
  }
}
async function _hydrateTrainingSessionSelect(formDef){
  if(!_isTrainingReflectionForm(formDef))return;
  var el=document.getElementById("mf_st");
  if(!el)return;
  var sessions=await _getTrainingSessions();
  var cur=el.value||"";
  var sel=document.createElement("select");
  sel.id=el.id;
  sel.required=true;
  var first=document.createElement("option");
  first.value="";
  first.textContent="請選擇課程";
  sel.appendChild(first);
  sessions.forEach(function(s){
    var o=document.createElement("option");
    o.value=s.title;
    o.textContent=s.date?(s.title+"｜"+s.date):s.title;
    if(cur&&cur===s.title)o.selected=true;
    sel.appendChild(o);
  });
  el.replaceWith(sel);
}
async function _hydratePromoSelect(formDef){
  if(!_isPromoSelectForm(formDef))return;
  var el=document.getElementById("mf_id");
  if(!el)return;
  var promos=await _getCoursePromos();
  var cur=el.value||"";
  var sel=document.createElement("select");
  sel.id=el.id;
  sel.required=true;
  var first=document.createElement("option");
  first.value="";
  first.textContent="請選擇文宣";
  sel.appendChild(first);
  promos.forEach(function(p){
    var o=document.createElement("option");
    o.value=p.id;
    o.textContent=(p.title||"").trim() ? (p.id+"｜"+p.title) : p.id;
    if(cur&&cur===p.id)o.selected=true;
    sel.appendChild(o);
  });
  el.replaceWith(sel);
}
async function _prefillPartnerForm(name){
  if(!name)return;
  var r=await fetch("/api/partner/"+encodeURIComponent(name));
  if(!r.ok)return;
  var d=await r.json();
  var p=(d&&d.result)||null;
  if(!p)return;
  var map={
    l:p.level||"",
    s:p.stage||"",
    d:p.next_followup||"",
    ci:p.contact_info||"",
    r:p.note||"",
    t:p.type||"",
    no:p.amway_no||"",
    p:p.partner||"",
    sp:p.sponsor||"",
    ed:p.expire_date||"",
    ym:p.year_month||"",
    rt:p.recent_title||"",
    fb:p.first_bonus_percent||"",
    cv:p.cash_voucher||"",
    sp2:p.shopping_points||"",
    cp:p.coupon||"",
    m1:(p.purchase_flags&&p.purchase_flags.this_month)||"",
    m2:(p.purchase_flags&&p.purchase_flags.last_month)||"",
    m3:(p.purchase_flags&&p.purchase_flags.prev2_month)||"",
    m4:(p.purchase_flags&&p.purchase_flags.prev3_month)||"",
    cg:p.category||""
  };
  Object.keys(map).forEach(function(k){
    var el=document.getElementById("mf_"+k);
    if(el && !el.dataset.userEdited){el.value=map[k];}
  });
}
function clickItem(item){
  if(item.cmd&&!item.form){doSend(item.cmd);}
  else if(item.form){openModal(item.form);}
}
function openModal(f){
  _build=f.build;
  document.getElementById("mtitletext").textContent=f.title||"";
  var mf=document.getElementById("mfields");mf.innerHTML="";
  f.fields.forEach(function(fd){
    var w=document.createElement("div");w.className="mf";
    var l=document.createElement("label");
    l.textContent=fd.lbl+(fd.req?" *":"");l.setAttribute("for","mf_"+fd.id);
    w.appendChild(l);
    var el;
    if(fd.type==="select"){
      el=document.createElement("select");el.id="mf_"+fd.id;
      if(!fd.req){var o=document.createElement("option");o.value="";o.textContent="（選填）";el.appendChild(o);}
      (fd.opts||fd.options||[]).forEach(function(o){var oe=document.createElement("option");if(typeof o==="object"&&o!==null){oe.value=(o.v!==undefined?o.v:(o.value!==undefined?o.value:""));oe.textContent=(o.l!==undefined?o.l:(o.label!==undefined?o.label:oe.value));}else{oe.value=o;oe.textContent=o;}el.appendChild(oe);});
    } else if(fd.type==="textarea"){
      el=document.createElement("textarea");el.id="mf_"+fd.id;
      el.placeholder=fd.ph||"";el.rows=3;
    } else {
      el=document.createElement("input");el.id="mf_"+fd.id;
      el.type=fd.type||"text";el.placeholder=fd.ph||"";
      if(fd.req)el.required=true;
      if(fd.type==="date")el.value=new Date().toISOString().split("T")[0];
    }
    el.addEventListener("input",function(){el.dataset.userEdited="1";});
    el.addEventListener("change",function(){el.dataset.userEdited="1";});
    w.appendChild(el);mf.appendChild(w);
  });
  document.getElementById("overlay").classList.add("on");
  _hydratePartnerSelect(f);
  _hydrateStoryPeopleSelect(f);
  _hydratePromoSelect(f);
  _hydrateTrainingModuleSelect(f);
  _hydrateTrainingSessionSelect(f);
  var first=mf.querySelector("input,select,textarea");
  if(first)setTimeout(function(){first.focus();},120);
}
function closeModal(){
  document.getElementById("overlay").classList.remove("on");_build=null;
}
function submitModal(){
  var mf=document.getElementById("mfields");
  var vals={};var ok=true;
  mf.querySelectorAll("input,select,textarea").forEach(function(el){
    var id=el.id.replace("mf_","");
    el.classList.remove("err");
    if(el.required&&!el.value.trim()){el.classList.add("err");ok=false;}
    else{vals[id]=el.value.trim();}
  });
  if(!ok){mf.querySelector(".err").focus();return;}
  var cmd=_build(vals);
  closeModal();doSend(cmd);
}
// Chat
function nt(){return new Date().toLocaleTimeString("zh-TW",{hour:"2-digit",minute:"2-digit"});}
function addMsg(text,role){
  var chat=document.getElementById("chat");
  var w=document.createElement("div");w.className="msg "+role;
  var b=document.createElement("div");b.className="bbl";b.textContent=text;
  var t=document.createElement("div");t.className="mt";t.textContent=nt();
  w.appendChild(b);w.appendChild(t);chat.appendChild(w);
  chat.scrollTop=chat.scrollHeight;return w;
}
function addSpin(){
  var chat=document.getElementById("chat");
  var w=document.createElement("div");w.className="msg b smsg";
  w.innerHTML='<div class="bbl"><div class="spin"></div><span>處理中…</span></div>';
  chat.appendChild(w);chat.scrollTop=chat.scrollHeight;return w;
}
function setBusy(on){
  document.getElementById("dot").className=on?"busy":"";
  document.getElementById("sendbtn").disabled=on;
  document.getElementById("inp").disabled=on;
}
async function doSend(forced){
  var inp=document.getElementById("inp");
  var cmd=(forced!==undefined?forced:inp.value).trim();
  if(!cmd)return;
  if(forced===undefined)inp.value="";
  addMsg(cmd,"u");setBusy(true);var sp=addSpin();
  try{
    var r=await fetch("/api/command",{method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({command:cmd})});
    var d=await r.json();sp.remove();
    var txt=d.result||"（無回應）";
    addMsg(txt,"b");
    if(txt.startsWith("📋 邀約組合清單")){addInviteComboButtons(txt);}
    else if(txt.startsWith("📨 今日之後已產生的會議邀約文宣")){addInviteManageButtons(txt);}
    else if(txt.startsWith("🛠️ 邀約文宣管理")){addInviteManageActionButtons();}
    else if(txt.startsWith("📝 是否修改這份邀約文宣")){addInviteEditConfirmButtons();}
    else if(txt.startsWith("📋 潛在家人名單")){addListButtons(txt,"潛在家人詳情");}
    else if(txt.startsWith("👤 ")){var nm=txt.split("\\n")[0].replace("👤 ","").split(/[\s　]/)[0];if(nm)addDetailButtons(nm);}
  }catch(e){sp.remove();addMsg("⚠️ 連線失敗："+e.message,"b");}
  finally{setBusy(false);}
}
function addInviteManageButtons(txt){
  var chat=document.getElementById("chat");
  var w=document.createElement("div");w.className="msg b";
  var wrap=document.createElement("div");
  wrap.style.cssText="display:flex;flex-direction:column;gap:6px;padding:4px 0";
  txt.split("\\n").forEach(function(line){
    var m=line.match(/^(\d+)\.\s+(.+)/);
    if(!m)return;
    var n=m[1],desc=m[2];
    var b=document.createElement("button");
    b.style.cssText="background:#007AFF;color:#fff;border:none;border-radius:10px;padding:9px 14px;font-size:13px;cursor:pointer;text-align:left;width:100%";
    b.textContent=n+". "+desc+"  👉 管理這筆文宣";
    (function(ni){b.onclick=function(){doSend(ni);};})(n);
    wrap.appendChild(b);
  });
  if(wrap.children.length>0){w.appendChild(wrap);chat.appendChild(w);chat.scrollTop=chat.scrollHeight;}
}
function addInviteManageActionButtons(){
  var chat=document.getElementById("chat");
  var w=document.createElement("div");w.className="msg b";
  var wrap=document.createElement("div");
  wrap.style.cssText="display:flex;gap:8px;flex-wrap:wrap;padding:4px 0";
  [["1","📝 修改已產生文宣"],["2","🔁 強制重新產生"]].forEach(function(it){
    var b=document.createElement("button");
    b.style.cssText="background:#5856D6;color:#fff;border:none;border-radius:10px;padding:9px 14px;font-size:13px;cursor:pointer";
    b.textContent=it[1];
    b.onclick=function(){doSend(it[0]);};
    wrap.appendChild(b);
  });
  w.appendChild(wrap);chat.appendChild(w);chat.scrollTop=chat.scrollHeight;
}
function addInviteEditConfirmButtons(){
  var chat=document.getElementById("chat");
  var w=document.createElement("div");w.className="msg b";
  var wrap=document.createElement("div");
  wrap.style.cssText="display:flex;gap:8px;flex-wrap:wrap;padding:4px 0";
  [["1","✅ 確定修改"],["2","取消"]].forEach(function(it){
    var b=document.createElement("button");
    b.style.cssText="background:#34C759;color:#fff;border:none;border-radius:10px;padding:9px 14px;font-size:13px;cursor:pointer";
    if(it[0]==="2"){b.style.background="#8E8E93";}
    b.textContent=it[1];
    b.onclick=function(){doSend(it[0]);};
    wrap.appendChild(b);
  });
  w.appendChild(wrap);chat.appendChild(w);chat.scrollTop=chat.scrollHeight;
}
function addDetailButtons(name){
  var chat=document.getElementById("chat");
  var w=document.createElement("div");w.className="msg b";
  var wrap=document.createElement("div");wrap.style.cssText="display:flex;gap:8px;flex-wrap:wrap;padding:4px 0";
  var eb=document.createElement("button");
  eb.style.cssText="background:#34C759;color:#fff;border:none;border-radius:10px;padding:9px 14px;font-size:13px;cursor:pointer";
  eb.textContent="✏️ 編輯基本資料";eb.onclick=function(){openEditProspect(name);};
  var xb=document.createElement("button");
  xb.style.cssText="background:#FF9500;color:#fff;border:none;border-radius:10px;padding:9px 14px;font-size:13px;cursor:pointer";
  xb.textContent="📝 新增體驗記錄";xb.onclick=function(){openAddExperience(name);};
  wrap.appendChild(eb);wrap.appendChild(xb);w.appendChild(wrap);
  chat.appendChild(w);chat.scrollTop=chat.scrollHeight;
}
async function openEditProspect(name){
  setBusy(true);
  try{
    var r=await fetch("/api/prospect/"+encodeURIComponent(name));
    var d=await r.json();var row=d.result||{};
    document.getElementById("mtitletext").textContent="✏️ 維護 "+name+" 的資料";
    var mf=document.getElementById("mfields");mf.innerHTML="";
    [{id:"電話",lbl:"電話",type:"text",ph:"手機號碼"},
     {id:"地區",lbl:"地區",type:"text",ph:"例：台中市西屯區"},
     {id:"地址",lbl:"地址",type:"text",ph:"完整地址"},
     {id:"接觸狀態",lbl:"接觸狀態",type:"text",ph:"例：持續跟進"},
     {id:"下次跟進日",lbl:"下次跟進日期",type:"date"},
     {id:"使用產品",lbl:"使用產品（逗號或頓號分隔）",type:"text",ph:"例：益生菌、魚油"},
     {id:"淨水器型號",lbl:"淨水器型號",type:"text",ph:"例：eSpring E-9255"},
     {id:"濾心上次換",lbl:"濾心上次更換日期",type:"date"},
     {id:"濾心下次換",lbl:"濾心下次更換日期",type:"date"},
     {id:"備註",lbl:"備註",type:"textarea"}
    ].forEach(function(fd){
      var ww=document.createElement("div");ww.className="mf";
      var l=document.createElement("label");l.textContent=fd.lbl;ww.appendChild(l);
      var el;
      if(fd.type==="textarea"){el=document.createElement("textarea");el.rows=3;}
      else{el=document.createElement("input");el.type=fd.type;}
      el.id="mf_"+fd.id;el.placeholder=fd.ph||"";
      el.value=row[fd.id]||"";
      ww.appendChild(el);mf.appendChild(ww);
    });
    document.getElementById("overlay").classList.add("on");
    document.getElementById("mok").onclick=async function(){
      var updates={name:name};
      mf.querySelectorAll("input,textarea").forEach(function(el){updates[el.id.replace("mf_","")]=el.value.trim();});
      document.getElementById("overlay").classList.remove("on");
      document.getElementById("mok").onclick=submitModal;
      setBusy(true);var sp=addSpin();
      try{var r2=await fetch("/api/prospect/update",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(updates)});
        var d2=await r2.json();sp.remove();addMsg(d2.result||"（已更新）","b");
      }catch(e){sp.remove();addMsg("⚠️ "+e.message,"b");}finally{setBusy(false);}
    };
  }catch(e){addMsg("⚠️ 載入失敗："+e.message,"b");}
  finally{setBusy(false);}
}
function openAddExperience(name){
  document.getElementById("mtitletext").textContent="📝 新增體驗記錄 — "+name;
  var mf=document.getElementById("mfields");mf.innerHTML="";
  [{id:"product",lbl:"產品/食品名稱",type:"text",req:1,ph:"例：益生菌、魚油、eSpring"},
   {id:"note",lbl:"備註",type:"textarea",ph:"例：每天早上服用 2 顆，效果明顯"},
   {id:"filter_last",lbl:"濾心上次更換（若適用）",type:"date"},
   {id:"filter_next",lbl:"濾心下次更換（若適用）",type:"date"}
  ].forEach(function(fd){
    var ww=document.createElement("div");ww.className="mf";
    var l=document.createElement("label");l.textContent=fd.lbl+(fd.req?" *":"");ww.appendChild(l);
    var el;
    if(fd.type==="textarea"){el=document.createElement("textarea");el.rows=3;}
    else{el=document.createElement("input");el.type=fd.type;}
    el.id="mfe_"+fd.id;el.placeholder=fd.ph||"";if(fd.req)el.required=true;
    ww.appendChild(el);mf.appendChild(ww);
  });
  document.getElementById("overlay").classList.add("on");
  var first=mf.querySelector("input");if(first)setTimeout(function(){first.focus();},120);
  document.getElementById("mok").onclick=async function(){
    var prod=document.getElementById("mfe_product");
    if(!prod.value.trim()){prod.classList.add("err");prod.focus();return;}
    var body={name:name,product:prod.value.trim(),
      note:(document.getElementById("mfe_note")||{}).value||"",
      filter_last:(document.getElementById("mfe_filter_last")||{}).value||"",
      filter_next:(document.getElementById("mfe_filter_next")||{}).value||""};
    document.getElementById("overlay").classList.remove("on");
    document.getElementById("mok").onclick=submitModal;
    setBusy(true);var sp=addSpin();
    try{var r=await fetch("/api/prospect/experience",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
      var d=await r.json();sp.remove();addMsg(d.result||"（已記錄）","b");
    }catch(e){sp.remove();addMsg("⚠️ "+e.message,"b");}finally{setBusy(false);}
  };
}
function addInviteComboButtons(txt){
  var chat=document.getElementById("chat");
  var w=document.createElement("div");w.className="msg b";
  var wrap=document.createElement("div");
  wrap.style.cssText="display:flex;flex-direction:column;gap:6px;padding:4px 0";
  txt.split("\\n").forEach(function(line){
    var m=line.match(/^(\d+)\.\s+(.+)/);
    if(!m)return;
    var n=m[1];var rawDesc=m[2];
    // Parse EXISTS marker
    var existsMatch=rawDesc.match(/\[EXISTS:([^:]+):(.+)\]$/);
    var hasInvite=!!existsMatch;
    var meetingId=hasInvite?existsMatch[1]:"";
    var personName=hasInvite?existsMatch[2]:"";
    var desc=rawDesc.replace(/\[EXISTS:[^\]]+\]$/,"").trim();
    var row=document.createElement("div");
    row.style.cssText="display:flex;gap:6px;align-items:center";
    var btn=document.createElement("button");
    if(hasInvite){
      btn.style.cssText="background:#34C759;color:#fff;border:none;border-radius:10px;padding:9px 14px;font-size:13px;cursor:pointer;text-align:left;flex:1";
      btn.textContent=n+". "+desc+" 👉 觀看已產生的邀約文宣";
      (function(mid,pname){
        btn.onclick=function(){openInviteModal(mid,pname);};
      })(meetingId,personName);
      var genBtn=document.createElement("button");
      genBtn.style.cssText="background:#5856D6;color:#fff;border:none;border-radius:10px;padding:9px 12px;font-size:12px;cursor:pointer;white-space:nowrap";
      genBtn.textContent="重新產生";
      (function(ni){genBtn.onclick=function(){doSend(ni);};})(n);
      row.appendChild(btn);row.appendChild(genBtn);
    } else {
      btn.style.cssText="background:#5856D6;color:#fff;border:none;border-radius:10px;padding:9px 14px;font-size:13px;cursor:pointer;text-align:left;flex:1";
      btn.textContent=n+". "+desc+" 👉 產生邀約文宣";
      (function(ni){btn.onclick=function(){doSend(ni);};})(n);
      row.appendChild(btn);
    }
    wrap.appendChild(row);
  });
  if(wrap.children.length>0){w.appendChild(wrap);chat.appendChild(w);chat.scrollTop=chat.scrollHeight;}
}
async function openInviteModal(meetingId,name){
  var r=await fetch("/api/course-invite?id="+encodeURIComponent(meetingId)+"&name="+encodeURIComponent(name));
  var d=await r.json();
  if(!d.result){addMsg("⚠️ 找不到邀約記錄","b");return;}
  var rec=d.result;
  // Build modal
  var ov=document.createElement("div");
  ov.style.cssText="position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:2000;display:flex;align-items:center;justify-content:center";
  var box=document.createElement("div");
  box.style.cssText="background:#fff;border-radius:16px;padding:24px;width:min(92vw,560px);display:flex;flex-direction:column;gap:12px;max-height:80vh";
  var title=document.createElement("div");
  title.style.cssText="font-weight:700;font-size:16px;color:#1c1c1e";
  title.textContent="邀約文宣 — "+name;
  var ta=document.createElement("textarea");
  ta.style.cssText="width:100%;flex:1;min-height:220px;border:1px solid #ddd;border-radius:10px;padding:10px;font-size:14px;resize:vertical;font-family:inherit;box-sizing:border-box";
  ta.value=rec.content||"";
  var meta=document.createElement("div");
  meta.style.cssText="font-size:11px;color:#8e8e93";
  meta.textContent="最後更新："+(rec.updated_at||"").replace("T"," ").slice(0,16);
  var btns=document.createElement("div");
  btns.style.cssText="display:flex;gap:10px;justify-content:flex-end";
  var saveBtn=document.createElement("button");
  saveBtn.style.cssText="background:#007AFF;color:#fff;border:none;border-radius:10px;padding:10px 20px;font-size:14px;cursor:pointer";
  saveBtn.textContent="儲存修改";
  saveBtn.onclick=async function(){
    var res=await fetch("/api/course-invite/update",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({meeting_id:meetingId,name:name,content:ta.value.trim()})});
    var rd=await res.json();
    addMsg(rd.result||"✅ 已更新","b");
    document.body.removeChild(ov);
  };
  var closeBtn=document.createElement("button");
  closeBtn.style.cssText="background:#f2f2f7;color:#1c1c1e;border:none;border-radius:10px;padding:10px 20px;font-size:14px;cursor:pointer";
  closeBtn.textContent="關閉";
  closeBtn.onclick=function(){document.body.removeChild(ov);};
  btns.appendChild(closeBtn);btns.appendChild(saveBtn);
  box.appendChild(title);box.appendChild(ta);box.appendChild(meta);box.appendChild(btns);
  ov.appendChild(box);
  ov.onclick=function(e){if(e.target===ov)document.body.removeChild(ov);};
  document.body.appendChild(ov);
  setTimeout(function(){ta.focus();},100);
}
function addListButtons(txt,prefix){
  var chat=document.getElementById("chat");
  var w=document.createElement("div");w.className="msg b";
  var wrap=document.createElement("div");
  wrap.style.cssText="display:flex;flex-direction:column;gap:6px;padding:4px 0";
  txt.split("\\n").forEach(function(line){
    var m=line.match(/^(\d+)\./);
    if(!m)return;
    var n=parseInt(m[1]);
    var btn=document.createElement("button");
    btn.style.cssText="background:var(--blue);color:#fff;border:none;border-radius:10px;padding:9px 14px;font-size:13px;cursor:pointer;text-align:left;width:100%";
    btn.textContent=line.trim()+" 👉 查看詳情";
    btn.onclick=function(){doSend(prefix+" "+n);};
    wrap.appendChild(btn);
  });
  if(wrap.children.length>0){w.appendChild(wrap);chat.appendChild(w);chat.scrollTop=chat.scrollHeight;}
}
// Upload
document.getElementById("finput").addEventListener("change",async function(){
  var f=this.files[0];if(!f)return;this.value="";
  addMsg("📎 "+f.name,"u");setBusy(true);var sp=addSpin();
  var fd=new FormData();fd.append("file",f,f.name);
  try{
    var r=await fetch("/api/upload",{method:"POST",body:fd});
    var d=await r.json();sp.remove();
    if(d.result){addMsg(d.result,"b");await refreshPend();}
    else{addMsg("✅ 上傳完成","b");}
  }catch(e){sp.remove();addMsg("⚠️ 上傳失敗："+e.message,"b");}
  finally{setBusy(false);}
});
// Pending
async function refreshPend(){
  try{var r=await fetch("/api/pending");var d=await r.json();
    if(d.result){showPend(d.result);}else{hidePend();}}catch(e){}
}
function showPend(txt){
  var btns=document.getElementById("pendbtns");btns.innerHTML="";
  txt.split("\\n").forEach(function(line){
    var m=line.match(/^(\\d+)[.)、:：]/);
    if(m){var n=parseInt(m[1]);
      var b=document.createElement("button");b.className="pbtn";
      b.textContent=line.trim();b.onclick=function(){execPend(n);};btns.appendChild(b);}
  });
  var cb=document.createElement("button");cb.className="pbtn cancel";
  cb.textContent="✕ 取消";cb.onclick=function(){execPend(0);hidePend();};btns.appendChild(cb);
  document.getElementById("pend").classList.add("on");
}
function hidePend(){
  document.getElementById("pend").classList.remove("on");
  document.getElementById("pendbtns").innerHTML="";
}
async function execPend(n){
  setBusy(true);var sp=addSpin();
  try{var r=await fetch("/api/pending/execute",{method:"POST",
      headers:{"Content-Type":"application/json"},body:JSON.stringify({choice:n})});
    var d=await r.json();sp.remove();addMsg(d.result||"（已執行）","b");hidePend();
  }catch(e){sp.remove();addMsg("⚠️ 執行失敗："+e.message,"b");}
  finally{setBusy(false);}
}
// Init
addMsg("你好！我是 Yisheng 助理 🤖\\n手機：點右下角 ☰ 開啟選單\\n電腦：點左側選單按鈕\\n上傳檔案：點 📎 按鈕","b");
refreshPend();
</script>
</body>
</html>"""


def _load_ai_prompt_manager():
    import importlib.util as _ilu
    from pathlib import Path

    path = Path(r"C:\Users\user\claude AI_Agent") / "agents" / "20_ai_prompt_manager.py"
    spec = _ilu.spec_from_file_location("ai_prompt_manager", str(path))
    module = _ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_ORIGINAL_RENDER_DASHBOARD_HTML_V2 = render_dashboard_html_v2


def render_dashboard_html_v2() -> str:
    html = _ORIGINAL_RENDER_DASHBOARD_HTML_V2()
    try:
        import json as _json

        pm = _load_ai_prompt_manager()
        prompt_items = pm.list_prompt_labels()
        prompt_json = _json.dumps(prompt_items, ensure_ascii=False)
    except Exception:
        prompt_json = "[]"

    inject = f"""
<script>
(function(){{
  const promptItems = {prompt_json};

  function addAIPromptButtons() {{
    const sidebar = document.getElementById("sidebar");
    const mobcont = document.getElementById("mobcont");
    if (!sidebar || !mobcont || document.getElementById("ai-prompt-group")) return;

    const makeItem = (label, direct, onclick) => {{
      const btn = document.createElement("button");
      btn.className = "sbtn" + (direct ? " direct" : " form-btn");
      btn.innerHTML = '<span class="lbl">'+label+'</span><span class="tag">'+(direct ? '直接' : '表單')+'</span>';
      btn.onclick = onclick;
      return btn;
    }};

    const group = document.createElement("div");
    group.className = "sg";
    group.id = "ai-prompt-group";
    group.innerHTML = '<div class="sghdr open"><span>🤖 AI 提示詞</span><span class="arr">▶</span></div><div class="sgitems open"></div>';
    const items = group.querySelector(".sgitems");
    items.appendChild(makeItem("查詢AI提示詞", true, () => doSend("查詢AI提示詞")));
    items.appendChild(makeItem("修改AI提示詞", false, openAIPromptModal));
    sidebar.appendChild(group);

    const mg = document.createElement("div");
    mg.className = "mgg";
    mg.innerHTML = '<div class="mgghdr">🤖 AI 提示詞</div>';
    const makeMobile = (label, direct, onclick) => {{
      const btn = document.createElement("button");
      btn.className = "mgbtn" + (direct ? " direct" : " form-btn");
      btn.innerHTML = '<span class="lbl">'+label+'</span><span class="mtag">'+(direct ? '直接' : '表單')+'</span>';
      btn.onclick = onclick;
      return btn;
    }};
    mg.appendChild(makeMobile("查詢AI提示詞", true, () => {{ closeMob(); doSend("查詢AI提示詞"); }}));
    mg.appendChild(makeMobile("修改AI提示詞", false, () => {{ closeMob(); openAIPromptModal(); }}));
    mobcont.appendChild(mg);
  }}

  function openAIPromptModal() {{
    openModal({{
      title: "修改AI提示詞",
      fields: [
        {{
          id: "k",
          lbl: "提示詞 key",
          type: "select",
          req: 1,
          options: promptItems.map(x => ({{ value: x.key, label: x.key + "｜" + x.label }}))
        }},
        {{
          id: "t",
          lbl: "新內容",
          type: "textarea",
          req: 1,
          ph: "系統會先載入目前提示詞內容，你再決定是否修改"
        }}
      ],
      build: function(v) {{
        return "更新AI提示詞 " + v.k + " | " + v.t;
      }}
    }});

    const keyField = document.getElementById("mf_k");
    const textField = document.getElementById("mf_t");
    const fieldsWrap = document.getElementById("mfields");
    if (!keyField || !textField || !fieldsWrap) return;

    let preview = document.getElementById("ai-prompt-preview");
    if (!preview) {{
      preview = document.createElement("div");
      preview.id = "ai-prompt-preview";
      preview.style.cssText = "font-size:12px;color:#6c6c70;line-height:1.6;background:#f2f2f7;border-radius:10px;padding:10px;white-space:pre-wrap";
      fieldsWrap.insertBefore(preview, textField.parentElement);
    }}

    async function loadCurrentPrompt() {{
      const key = keyField.value;
      preview.textContent = "正在載入目前提示詞...";
      try {{
        const r = await fetch("/api/ai-prompt/" + encodeURIComponent(key));
        const d = await r.json();
        if (!d.result) {{
          preview.textContent = "找不到這組提示詞。";
          return;
        }}
        const item = d.result;
        preview.textContent =
          "目前提示詞預覽\\n" +
          "key: " + key + "\\n" +
          "名稱: " + (item.label || "") + "\\n" +
          "說明: " + (item.description || "") + "\\n\\n" +
          (item.template || "");
        textField.value = item.template || "";
      }} catch (e) {{
        preview.textContent = "載入目前提示詞失敗：" + e.message;
      }}
    }}

    keyField.onchange = loadCurrentPrompt;
    loadCurrentPrompt();
  }}

  window.openAIPromptModal = openAIPromptModal;
  if (document.readyState === "loading") {{
    document.addEventListener("DOMContentLoaded", addAIPromptButtons);
  }} else {{
    addAIPromptButtons();
  }}
}})();
</script>
"""

    inject += """
<script>
(function(){
  async function fetchJson(url){
    try {
      const r = await fetch(url);
      return await r.json();
    } catch (e) {
      return {};
    }
  }

  async function loadTrainingData(){
    const [mods, sessions, partners] = await Promise.all([
      fetchJson('/api/training-modules'),
      fetchJson('/api/training-sessions'),
      fetchJson('/api/partners')
    ]);
    return {
      modules: (mods.result || []).map(x => ({ value: x.title, label: x.title })),
      sessions: (sessions.result || []).map(x => ({ value: x.title, label: x.title })),
      partners: (partners.result || []).map(x => ({ value: x.name, label: x.name }))
    };
  }

  function makeSidebarItem(label, direct, onclick){
    const btn = document.createElement('button');
    btn.className = 'sbtn' + (direct ? ' direct' : ' form-btn');
    btn.innerHTML = '<span class="lbl">' + label + '</span><span class="tag">' + (direct ? '????' : '??') + '</span>';
    btn.onclick = onclick;
    return btn;
  }

  function makeMobileItem(label, direct, onclick){
    const btn = document.createElement('button');
    btn.className = 'mgbtn' + (direct ? ' direct' : ' form-btn');
    btn.innerHTML = '<span class="lbl">' + label + '</span><span class="mtag">' + (direct ? '????' : '??') + '</span>';
    btn.onclick = onclick;
    return btn;
  }

  async function openTrainingForm(kind){
    const data = await loadTrainingData();
    const defs = {
      module_add: {
        title: '??????',
        fields: [
          {id:'title', lbl:'????', type:'text', req:1},
          {id:'kind', lbl:'????', type:'text', req:1},
          {id:'goal', lbl:'????', type:'text', req:1},
          {id:'summary', lbl:'??', type:'textarea'}
        ],
        build: v => `?????? ${v.title} | ${v.kind} | ${v.goal} | ${v.summary || ''}`
      },
      session_add: {
        title: '??????',
        fields: [
          {id:'title', lbl:'????', type:'text', req:1},
          {id:'module', lbl:'????', type:'select', req:1, options:data.modules},
          {id:'date', lbl:'??', type:'text', req:1, ph:'2026-04-10'},
          {id:'time', lbl:'??', type:'text', req:1, ph:'19:30'},
          {id:'location', lbl:'??', type:'text'},
          {id:'teacher', lbl:'??', type:'text'},
          {id:'audience', lbl:'??', type:'text'}
        ],
        build: v => `?????? ${v.title} | ${v.module} | ${v.date} | ${v.time} | ${v.location || ''} | ${v.teacher || ''} | ${v.audience || ''}`
      },
      reflection_add: {
        title: '??????',
        fields: [
          {id:'name', lbl:'??', type:'select', req:1, options:data.partners},
          {id:'session', lbl:'????', type:'select', req:1, options:data.sessions},
          {id:'realize', lbl:'??', type:'textarea', req:1},
          {id:'learn', lbl:'??', type:'textarea', req:1},
          {id:'doit', lbl:'??', type:'textarea', req:1},
          {id:'goal', lbl:'??', type:'textarea', req:1}
        ],
        build: v => `?????? ${v.name} | ${v.session} | ${v.realize} | ${v.learn} | ${v.doit} | ${v.goal}`
      },
      progress_query: {
        title: '??????',
        fields: [{id:'name', lbl:'??', type:'select', req:1, options:data.partners}],
        build: v => `?????? ${v.name}`
      },
      seven_start: {
        title: '??????',
        fields: [
          {id:'name', lbl:'??', type:'select', req:1, options:data.partners},
          {id:'date', lbl:'????', type:'text', req:1, ph:'2026-04-10'},
          {id:'note', lbl:'????', type:'textarea'}
        ],
        build: v => `?????? ${v.name} | ${v.date} | ${v.note || ''}`
      },
      seven_report: {
        title: '??????',
        fields: [
          {id:'name', lbl:'??', type:'select', req:1, options:data.partners},
          {id:'day', lbl:'???', type:'text', req:1, ph:'?1?'},
          {id:'task', lbl:'????', type:'text', req:1},
          {id:'status', lbl:'??', type:'select', req:1, options:[{value:'???',label:'???'},{value:'???',label:'???'}]},
          {id:'note', lbl:'??', type:'textarea'}
        ],
        build: v => `?????? ${v.name} | ${v.day} | ${v.task} | ${v.status} | ${v.note || ''}`
      },
      seven_query: {
        title: '??????',
        fields: [{id:'name', lbl:'??', type:'select', req:1, options:data.partners}],
        build: v => `?????? ${v.name}`
      },
      action_add: {
        title: '??????',
        fields: [
          {id:'name', lbl:'??', type:'select', req:1, options:data.partners},
          {id:'session', lbl:'????', type:'select', req:1, options:data.sessions},
          {id:'action', lbl:'????', type:'textarea', req:1},
          {id:'deadline', lbl:'????', type:'text', req:1, ph:'2026-04-18'}
        ],
        build: v => `?????? ${v.name} | ${v.session} | ${v.action} | ${v.deadline}`
      },
      action_update: {
        title: '??????',
        fields: [
          {id:'name', lbl:'??', type:'select', req:1, options:data.partners},
          {id:'action_id', lbl:'ACTION-ID', type:'text', req:1},
          {id:'status', lbl:'??', type:'text', req:1},
          {id:'note', lbl:'??', type:'textarea'}
        ],
        build: v => `?????? ${v.name} | ${v.action_id} | ${v.status} | ${v.note || ''}`
      },
      action_query: {
        title: '??????',
        fields: [{id:'name', lbl:'??', type:'select', req:1, options:data.partners}],
        build: v => `?????? ${v.name}`
      }
    };
    openModal(defs[kind]);
  }

  function addTrainingButtons(){
    const sidebar = document.getElementById('sidebar');
    const mobcont = document.getElementById('mobcont');
    if (!sidebar || !mobcont || document.getElementById('training-system-clean-group')) return;

    const group = document.createElement('div');
    group.className = 'sg';
    group.id = 'training-system-clean-group';
    group.innerHTML = '<div class="sghdr open"><span>?? ???? 2.0</span><span class="arr">?</span></div><div class="sgitems open"></div>';
    const items = group.querySelector('.sgitems');
    const defs = [
      ['??????', false, () => openTrainingForm('module_add')],
      ['??????', true, () => doSend('??????')],
      ['??????', false, () => openTrainingForm('session_add')],
      ['??????', true, () => doSend('??????')],
      ['??????', false, () => openTrainingForm('reflection_add')],
      ['??????', false, () => openTrainingForm('progress_query')],
      ['??????', true, () => doSend('??????')],
      ['??????', false, () => openTrainingForm('seven_start')],
      ['??????', false, () => openTrainingForm('seven_report')],
      ['??????', false, () => openTrainingForm('seven_query')],
      ['??????', false, () => openTrainingForm('action_add')],
      ['??????', false, () => openTrainingForm('action_update')],
      ['??????', false, () => openTrainingForm('action_query')]
    ];
    defs.forEach(([label, direct, onclick]) => items.appendChild(makeSidebarItem(label, direct, onclick)));
    sidebar.appendChild(group);

    const mg = document.createElement('div');
    mg.className = 'mgg';
    mg.innerHTML = '<div class="mgghdr">?? ???? 2.0</div>';
    defs.forEach(([label, direct, onclick]) => mg.appendChild(makeMobileItem(label, direct, () => { closeMob(); onclick(); })));
    mobcont.appendChild(mg);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addTrainingButtons);
  } else {
    addTrainingButtons();
  }
})();
</script>
"""
    return html.replace("</body>", inject + "\n</body>")


_RENDER_WITH_AI_PROMPTS = render_dashboard_html_v2


def render_dashboard_html_v2() -> str:
    html = _RENDER_WITH_AI_PROMPTS()
    inject = """
<script>
(function(){
  async function fetchJson(url){
    const r = await fetch(url);
    const d = await r.json();
    return Array.isArray(d.result) ? d.result : [];
  }

  async function openFollowupSuggestionModal(kind){
    const isPartner = kind === "partner";
    const items = await fetchJson(isPartner ? "/api/partners" : "/api/prospects");
    if(!items.length){
      addMsg("目前沒有可選名單。","b");
      return;
    }
    const options = items.map(function(item){
      const name = item.name || "";
      const tail = isPartner
        ? [item.level || "", item.stage || "", item.category || ""].filter(Boolean).join(" / ")
        : [item.job || "", item.area || "", item.tag || item.status || ""].filter(Boolean).join(" / ");
      return { value:name, label: tail ? (name + "｜" + tail) : name };
    });
    openModal({
      title: isPartner ? "跟進建議－夥伴" : "跟進建議－潛在家人",
      fields: [
        { id:"n", lbl:"選擇對象", type:"select", req:1, options:options }
      ],
      build: function(v){
        return (isPartner ? "跟進建議 夥伴 " : "跟進建議 潛在家人 ") + v.n;
      }
    });
  }

  function addFollowupSuggestionButtons() {
    const sidebar = document.getElementById("sidebar");
    const mobcont = document.getElementById("mobcont");
    if (!sidebar || !mobcont || document.getElementById("followup-suggestion-group")) return;

    const makeItem = (label, onclick) => {
      const btn = document.createElement("button");
      btn.className = "sbtn form-btn";
      btn.innerHTML = '<span class="lbl">'+label+'</span><span class="tag">表單</span>';
      btn.onclick = onclick;
      return btn;
    };

    const group = document.createElement("div");
    group.className = "sg";
    group.id = "followup-suggestion-group";
    group.innerHTML = '<div class="sghdr open"><span>🧭 跟進建議</span><span class="arr">▶</span></div><div class="sgitems open"></div>';
    const items = group.querySelector(".sgitems");
    items.appendChild(makeItem("跟進建議－潛在家人", () => openFollowupSuggestionModal("prospect")));
    items.appendChild(makeItem("跟進建議－夥伴", () => openFollowupSuggestionModal("partner")));
    sidebar.appendChild(group);

    const makeMobile = (label, kind) => {
      const btn = document.createElement("button");
      btn.className = "mgbtn form-btn";
      btn.innerHTML = '<span class="lbl">'+label+'</span><span class="mtag">表單</span>';
      btn.onclick = function(){ closeMob(); openFollowupSuggestionModal(kind); };
      return btn;
    };
    const mg = document.createElement("div");
    mg.className = "mgg";
    mg.innerHTML = '<div class="mgghdr">🧭 跟進建議</div>';
    mg.appendChild(makeMobile("跟進建議－潛在家人", "prospect"));
    mg.appendChild(makeMobile("跟進建議－夥伴", "partner"));
    mobcont.appendChild(mg);
  }

  window.openFollowupSuggestionModal = openFollowupSuggestionModal;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", addFollowupSuggestionButtons);
  } else {
    addFollowupSuggestionButtons();
  }
})();
</script>
"""

    inject += """
<script>
(function(){
  async function fetchJson(url){
    try {
      const r = await fetch(url);
      return await r.json();
    } catch (e) {
      return {};
    }
  }

  async function loadTrainingData(){
    const [mods, sessions, partners] = await Promise.all([
      fetchJson('/api/training-modules'),
      fetchJson('/api/training-sessions'),
      fetchJson('/api/partners')
    ]);
    return {
      modules: (mods.result || []).map(x => ({ value: x.title, label: x.title })),
      sessions: (sessions.result || []).map(x => ({ value: x.title, label: x.title })),
      partners: (partners.result || []).map(x => ({ value: x.name, label: x.name }))
    };
  }

  function makeSidebarItem(label, direct, onclick){
    const btn = document.createElement('button');
    btn.className = 'sbtn' + (direct ? ' direct' : ' form-btn');
    btn.innerHTML = '<span class="lbl">' + label + '</span><span class="tag">' + (direct ? '????' : '??') + '</span>';
    btn.onclick = onclick;
    return btn;
  }

  function makeMobileItem(label, direct, onclick){
    const btn = document.createElement('button');
    btn.className = 'mgbtn' + (direct ? ' direct' : ' form-btn');
    btn.innerHTML = '<span class="lbl">' + label + '</span><span class="mtag">' + (direct ? '????' : '??') + '</span>';
    btn.onclick = onclick;
    return btn;
  }

  async function openTrainingForm(kind){
    const data = await loadTrainingData();
    const defs = {
      module_add: {
        title: '??????',
        fields: [
          {id:'title', lbl:'????', type:'text', req:1},
          {id:'kind', lbl:'????', type:'text', req:1},
          {id:'goal', lbl:'????', type:'text', req:1},
          {id:'summary', lbl:'??', type:'textarea'}
        ],
        build: v => `?????? ${v.title} | ${v.kind} | ${v.goal} | ${v.summary || ''}`
      },
      session_add: {
        title: '??????',
        fields: [
          {id:'title', lbl:'????', type:'text', req:1},
          {id:'module', lbl:'????', type:'select', req:1, options:data.modules},
          {id:'date', lbl:'??', type:'text', req:1, ph:'2026-04-10'},
          {id:'time', lbl:'??', type:'text', req:1, ph:'19:30'},
          {id:'location', lbl:'??', type:'text'},
          {id:'teacher', lbl:'??', type:'text'},
          {id:'audience', lbl:'??', type:'text'}
        ],
        build: v => `?????? ${v.title} | ${v.module} | ${v.date} | ${v.time} | ${v.location || ''} | ${v.teacher || ''} | ${v.audience || ''}`
      },
      reflection_add: {
        title: '??????',
        fields: [
          {id:'name', lbl:'??', type:'select', req:1, options:data.partners},
          {id:'session', lbl:'????', type:'select', req:1, options:data.sessions},
          {id:'realize', lbl:'??', type:'textarea', req:1},
          {id:'learn', lbl:'??', type:'textarea', req:1},
          {id:'doit', lbl:'??', type:'textarea', req:1},
          {id:'goal', lbl:'??', type:'textarea', req:1}
        ],
        build: v => `?????? ${v.name} | ${v.session} | ${v.realize} | ${v.learn} | ${v.doit} | ${v.goal}`
      },
      progress_query: {
        title: '??????',
        fields: [{id:'name', lbl:'??', type:'select', req:1, options:data.partners}],
        build: v => `?????? ${v.name}`
      },
      seven_start: {
        title: '??????',
        fields: [
          {id:'name', lbl:'??', type:'select', req:1, options:data.partners},
          {id:'date', lbl:'????', type:'text', req:1, ph:'2026-04-10'},
          {id:'note', lbl:'????', type:'textarea'}
        ],
        build: v => `?????? ${v.name} | ${v.date} | ${v.note || ''}`
      },
      seven_report: {
        title: '??????',
        fields: [
          {id:'name', lbl:'??', type:'select', req:1, options:data.partners},
          {id:'day', lbl:'???', type:'text', req:1, ph:'?1?'},
          {id:'task', lbl:'????', type:'text', req:1},
          {id:'status', lbl:'??', type:'select', req:1, options:[{value:'???',label:'???'},{value:'???',label:'???'}]},
          {id:'note', lbl:'??', type:'textarea'}
        ],
        build: v => `?????? ${v.name} | ${v.day} | ${v.task} | ${v.status} | ${v.note || ''}`
      },
      seven_query: {
        title: '??????',
        fields: [{id:'name', lbl:'??', type:'select', req:1, options:data.partners}],
        build: v => `?????? ${v.name}`
      },
      action_add: {
        title: '??????',
        fields: [
          {id:'name', lbl:'??', type:'select', req:1, options:data.partners},
          {id:'session', lbl:'????', type:'select', req:1, options:data.sessions},
          {id:'action', lbl:'????', type:'textarea', req:1},
          {id:'deadline', lbl:'????', type:'text', req:1, ph:'2026-04-18'}
        ],
        build: v => `?????? ${v.name} | ${v.session} | ${v.action} | ${v.deadline}`
      },
      action_update: {
        title: '??????',
        fields: [
          {id:'name', lbl:'??', type:'select', req:1, options:data.partners},
          {id:'action_id', lbl:'ACTION-ID', type:'text', req:1},
          {id:'status', lbl:'??', type:'text', req:1},
          {id:'note', lbl:'??', type:'textarea'}
        ],
        build: v => `?????? ${v.name} | ${v.action_id} | ${v.status} | ${v.note || ''}`
      },
      action_query: {
        title: '??????',
        fields: [{id:'name', lbl:'??', type:'select', req:1, options:data.partners}],
        build: v => `?????? ${v.name}`
      }
    };
    openModal(defs[kind]);
  }

  function addTrainingButtons(){
    const sidebar = document.getElementById('sidebar');
    const mobcont = document.getElementById('mobcont');
    if (!sidebar || !mobcont || document.getElementById('training-system-clean-group')) return;

    const group = document.createElement('div');
    group.className = 'sg';
    group.id = 'training-system-clean-group';
    group.innerHTML = '<div class="sghdr open"><span>?? ???? 2.0</span><span class="arr">?</span></div><div class="sgitems open"></div>';
    const items = group.querySelector('.sgitems');
    const defs = [
      ['??????', false, () => openTrainingForm('module_add')],
      ['??????', true, () => doSend('??????')],
      ['??????', false, () => openTrainingForm('session_add')],
      ['??????', true, () => doSend('??????')],
      ['??????', false, () => openTrainingForm('reflection_add')],
      ['??????', false, () => openTrainingForm('progress_query')],
      ['??????', true, () => doSend('??????')],
      ['??????', false, () => openTrainingForm('seven_start')],
      ['??????', false, () => openTrainingForm('seven_report')],
      ['??????', false, () => openTrainingForm('seven_query')],
      ['??????', false, () => openTrainingForm('action_add')],
      ['??????', false, () => openTrainingForm('action_update')],
      ['??????', false, () => openTrainingForm('action_query')]
    ];
    defs.forEach(([label, direct, onclick]) => items.appendChild(makeSidebarItem(label, direct, onclick)));
    sidebar.appendChild(group);

    const mg = document.createElement('div');
    mg.className = 'mgg';
    mg.innerHTML = '<div class="mgghdr">?? ???? 2.0</div>';
    defs.forEach(([label, direct, onclick]) => mg.appendChild(makeMobileItem(label, direct, () => { closeMob(); onclick(); })));
    mobcont.appendChild(mg);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addTrainingButtons);
  } else {
    addTrainingButtons();
  }
})();
</script>
"""
    return html.replace("</body>", inject + "\n</body>")


_RENDER_WITH_FOLLOWUP_SUGGESTION = render_dashboard_html_v2


def render_dashboard_html_v2() -> str:
    html = _RENDER_WITH_FOLLOWUP_SUGGESTION()
    inject = """
<script>
(function(){
  let partnerStatuses = null;

  async function getPartnerStatuses(){
    if(partnerStatuses) return partnerStatuses;
    const r = await fetch("/api/partner-statuses");
    const d = await r.json();
    partnerStatuses = Array.isArray(d.result) ? d.result : [];
    return partnerStatuses;
  }

  function replaceStatusFieldWithSelect(required){
    const oldEl = document.getElementById("mf_s");
    if(!oldEl) return;
    const wrap = oldEl.parentElement;
    if(!wrap || wrap.dataset.partnerStatusEnhanced==="1") return;
    getPartnerStatuses().then(function(items){
      const currentValue = oldEl.value || "";
      const sel = document.createElement("select");
      sel.id = oldEl.id;
      sel.required = !!required;
      sel.dataset.userEdited = oldEl.dataset.userEdited || "";
      const first = document.createElement("option");
      first.value = "";
      first.textContent = required ? "請選擇狀態" : "保留原狀態";
      sel.appendChild(first);
      items.forEach(function(item){
        const o = document.createElement("option");
        o.value = item.value;
        o.textContent = item.label + "｜" + item.description;
        if(currentValue && currentValue === item.value){ o.selected = true; }
        sel.appendChild(o);
      });
      sel.addEventListener("input", function(){ sel.dataset.userEdited = "1"; });
      sel.addEventListener("change", function(){ sel.dataset.userEdited = "1"; });
      oldEl.replaceWith(sel);
      wrap.dataset.partnerStatusEnhanced = "1";
    }).catch(function(){});
  }

  function injectPartnerStatusButton(){
    const sidebar = document.getElementById("sidebar");
    const mobcont = document.getElementById("mobcont");
    if(!sidebar || !mobcont || document.getElementById("partner-status-group")) return;

    const group = document.createElement("div");
    group.className = "sg";
    group.id = "partner-status-group";
    group.innerHTML = '<div class="sghdr open"><span>📚 夥伴狀態</span><span class="arr">▶</span></div><div class="sgitems open"></div>';
    const items = group.querySelector(".sgitems");

    const btn = document.createElement("button");
    btn.className = "sbtn direct";
    btn.innerHTML = '<span class="lbl">查詢夥伴狀態定義</span><span class="tag">直接</span>';
    btn.onclick = function(){ doSend("查詢夥伴狀態定義"); };
    items.appendChild(btn);
    sidebar.appendChild(group);

    const mg = document.createElement("div");
    mg.className = "mgg";
    mg.innerHTML = '<div class="mgghdr">📚 夥伴狀態</div>';
    const mb = document.createElement("button");
    mb.className = "mgbtn direct";
    mb.innerHTML = '<span class="lbl">查詢夥伴狀態定義</span><span class="mtag">直接</span>';
    mb.onclick = function(){ closeMob(); doSend("查詢夥伴狀態定義"); };
    mg.appendChild(mb);
    mobcont.appendChild(mg);
  }

  const originalOpenModal = window.openModal;
  window.openModal = function(f){
    originalOpenModal(f);
    const title = (f && f.title) || "";
    if(title.indexOf("更新夥伴") !== -1){
      setTimeout(function(){ replaceStatusFieldWithSelect(false); }, 0);
    } else if(title.indexOf("跟進夥伴") !== -1){
      setTimeout(function(){ replaceStatusFieldWithSelect(true); }, 0);
    }
  };

  if(document.readyState === "loading"){
    document.addEventListener("DOMContentLoaded", injectPartnerStatusButton);
  }else{
    injectPartnerStatusButton();
  }
})();
</script>
"""

    inject += """
<script>
(function(){
  async function fetchJson(url){
    try {
      const r = await fetch(url);
      return await r.json();
    } catch (e) {
      return {};
    }
  }

  async function loadTrainingData(){
    const [mods, sessions, partners] = await Promise.all([
      fetchJson('/api/training-modules'),
      fetchJson('/api/training-sessions'),
      fetchJson('/api/partners')
    ]);
    return {
      modules: (mods.result || []).map(x => ({ value: x.title, label: x.title })),
      sessions: (sessions.result || []).map(x => ({ value: x.title, label: x.title })),
      partners: (partners.result || []).map(x => ({ value: x.name, label: x.name }))
    };
  }

  function makeSidebarItem(label, direct, onclick){
    const btn = document.createElement('button');
    btn.className = 'sbtn' + (direct ? ' direct' : ' form-btn');
    btn.innerHTML = '<span class="lbl">' + label + '</span><span class="tag">' + (direct ? '????' : '??') + '</span>';
    btn.onclick = onclick;
    return btn;
  }

  function makeMobileItem(label, direct, onclick){
    const btn = document.createElement('button');
    btn.className = 'mgbtn' + (direct ? ' direct' : ' form-btn');
    btn.innerHTML = '<span class="lbl">' + label + '</span><span class="mtag">' + (direct ? '????' : '??') + '</span>';
    btn.onclick = onclick;
    return btn;
  }

  async function openTrainingForm(kind){
    const data = await loadTrainingData();
    const defs = {
      module_add: {
        title: '??????',
        fields: [
          {id:'title', lbl:'????', type:'text', req:1},
          {id:'kind', lbl:'????', type:'text', req:1},
          {id:'goal', lbl:'????', type:'text', req:1},
          {id:'summary', lbl:'??', type:'textarea'}
        ],
        build: v => `?????? ${v.title} | ${v.kind} | ${v.goal} | ${v.summary || ''}`
      },
      session_add: {
        title: '??????',
        fields: [
          {id:'title', lbl:'????', type:'text', req:1},
          {id:'module', lbl:'????', type:'select', req:1, options:data.modules},
          {id:'date', lbl:'??', type:'text', req:1, ph:'2026-04-10'},
          {id:'time', lbl:'??', type:'text', req:1, ph:'19:30'},
          {id:'location', lbl:'??', type:'text'},
          {id:'teacher', lbl:'??', type:'text'},
          {id:'audience', lbl:'??', type:'text'}
        ],
        build: v => `?????? ${v.title} | ${v.module} | ${v.date} | ${v.time} | ${v.location || ''} | ${v.teacher || ''} | ${v.audience || ''}`
      },
      reflection_add: {
        title: '??????',
        fields: [
          {id:'name', lbl:'??', type:'select', req:1, options:data.partners},
          {id:'session', lbl:'????', type:'select', req:1, options:data.sessions},
          {id:'realize', lbl:'??', type:'textarea', req:1},
          {id:'learn', lbl:'??', type:'textarea', req:1},
          {id:'doit', lbl:'??', type:'textarea', req:1},
          {id:'goal', lbl:'??', type:'textarea', req:1}
        ],
        build: v => `?????? ${v.name} | ${v.session} | ${v.realize} | ${v.learn} | ${v.doit} | ${v.goal}`
      },
      progress_query: {
        title: '??????',
        fields: [{id:'name', lbl:'??', type:'select', req:1, options:data.partners}],
        build: v => `?????? ${v.name}`
      },
      seven_start: {
        title: '??????',
        fields: [
          {id:'name', lbl:'??', type:'select', req:1, options:data.partners},
          {id:'date', lbl:'????', type:'text', req:1, ph:'2026-04-10'},
          {id:'note', lbl:'????', type:'textarea'}
        ],
        build: v => `?????? ${v.name} | ${v.date} | ${v.note || ''}`
      },
      seven_report: {
        title: '??????',
        fields: [
          {id:'name', lbl:'??', type:'select', req:1, options:data.partners},
          {id:'day', lbl:'???', type:'text', req:1, ph:'?1?'},
          {id:'task', lbl:'????', type:'text', req:1},
          {id:'status', lbl:'??', type:'select', req:1, options:[{value:'???',label:'???'},{value:'???',label:'???'}]},
          {id:'note', lbl:'??', type:'textarea'}
        ],
        build: v => `?????? ${v.name} | ${v.day} | ${v.task} | ${v.status} | ${v.note || ''}`
      },
      seven_query: {
        title: '??????',
        fields: [{id:'name', lbl:'??', type:'select', req:1, options:data.partners}],
        build: v => `?????? ${v.name}`
      },
      action_add: {
        title: '??????',
        fields: [
          {id:'name', lbl:'??', type:'select', req:1, options:data.partners},
          {id:'session', lbl:'????', type:'select', req:1, options:data.sessions},
          {id:'action', lbl:'????', type:'textarea', req:1},
          {id:'deadline', lbl:'????', type:'text', req:1, ph:'2026-04-18'}
        ],
        build: v => `?????? ${v.name} | ${v.session} | ${v.action} | ${v.deadline}`
      },
      action_update: {
        title: '??????',
        fields: [
          {id:'name', lbl:'??', type:'select', req:1, options:data.partners},
          {id:'action_id', lbl:'ACTION-ID', type:'text', req:1},
          {id:'status', lbl:'??', type:'text', req:1},
          {id:'note', lbl:'??', type:'textarea'}
        ],
        build: v => `?????? ${v.name} | ${v.action_id} | ${v.status} | ${v.note || ''}`
      },
      action_query: {
        title: '??????',
        fields: [{id:'name', lbl:'??', type:'select', req:1, options:data.partners}],
        build: v => `?????? ${v.name}`
      }
    };
    openModal(defs[kind]);
  }

  function addTrainingButtons(){
    const sidebar = document.getElementById('sidebar');
    const mobcont = document.getElementById('mobcont');
    if (!sidebar || !mobcont || document.getElementById('training-system-clean-group')) return;

    const group = document.createElement('div');
    group.className = 'sg';
    group.id = 'training-system-clean-group';
    group.innerHTML = '<div class="sghdr open"><span>?? ???? 2.0</span><span class="arr">?</span></div><div class="sgitems open"></div>';
    const items = group.querySelector('.sgitems');
    const defs = [
      ['??????', false, () => openTrainingForm('module_add')],
      ['??????', true, () => doSend('??????')],
      ['??????', false, () => openTrainingForm('session_add')],
      ['??????', true, () => doSend('??????')],
      ['??????', false, () => openTrainingForm('reflection_add')],
      ['??????', false, () => openTrainingForm('progress_query')],
      ['??????', true, () => doSend('??????')],
      ['??????', false, () => openTrainingForm('seven_start')],
      ['??????', false, () => openTrainingForm('seven_report')],
      ['??????', false, () => openTrainingForm('seven_query')],
      ['??????', false, () => openTrainingForm('action_add')],
      ['??????', false, () => openTrainingForm('action_update')],
      ['??????', false, () => openTrainingForm('action_query')]
    ];
    defs.forEach(([label, direct, onclick]) => items.appendChild(makeSidebarItem(label, direct, onclick)));
    sidebar.appendChild(group);

    const mg = document.createElement('div');
    mg.className = 'mgg';
    mg.innerHTML = '<div class="mgghdr">?? ???? 2.0</div>';
    defs.forEach(([label, direct, onclick]) => mg.appendChild(makeMobileItem(label, direct, () => { closeMob(); onclick(); })));
    mobcont.appendChild(mg);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addTrainingButtons);
  } else {
    addTrainingButtons();
  }
})();
</script>
"""
    return html.replace("</body>", inject + "\n</body>")


try:
    import importlib.util as _ilu
    from pathlib import Path as _Path
except Exception:  # pragma: no cover
    _ilu = None
    _Path = None


def _load_ai_skill_manager():
    if _ilu is None or _Path is None:
        raise RuntimeError("ai skill loader unavailable")
    path = _Path(r"C:\Users\user\claude AI_Agent") / "agents" / "22_ai_skill_manager.py"
    spec = _ilu.spec_from_file_location("ai_skill_manager", str(path))
    module = _ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_RENDER_WITH_PARTNER_STATUS = render_dashboard_html_v2


def render_dashboard_html_v2() -> str:
    html = _RENDER_WITH_PARTNER_STATUS()
    try:
        import json as _json

        sm = _load_ai_skill_manager()
        skill_items = sm.list_skill_labels()
        skill_json = _json.dumps(skill_items, ensure_ascii=False)
    except Exception:
        skill_json = "[]"

    inject = f"""
<script>
(function(){{
  const skillItems = {skill_json};

  function addAISkillButtons() {{
    const sidebar = document.getElementById("sidebar");
    const mobcont = document.getElementById("mobcont");
    if (!sidebar || !mobcont || document.getElementById("ai-skill-group")) return;

    const makeItem = (label, direct, onclick) => {{
      const btn = document.createElement("button");
      btn.className = "sbtn" + (direct ? " direct" : " form-btn");
      btn.innerHTML = '<span class="lbl">'+label+'</span><span class="tag">'+(direct ? '直接執行' : '表單')+'</span>';
      btn.onclick = onclick;
      return btn;
    }};

    const group = document.createElement("div");
    group.className = "sg";
    group.id = "ai-skill-group";
    group.innerHTML = '<div class="sghdr open"><span>🧠 AI 技能</span><span class="arr">▶</span></div><div class="sgitems open"></div>';
    const items = group.querySelector(".sgitems");
    items.appendChild(makeItem("查詢AI技能", true, () => doSend("查詢AI技能")));
    items.appendChild(makeItem("修改AI技能", false, openAISkillModal));
    sidebar.appendChild(group);

    const makeMobile = (label, direct, onclick) => {{
      const btn = document.createElement("button");
      btn.className = "mgbtn" + (direct ? " direct" : " form-btn");
      btn.innerHTML = '<span class="lbl">'+label+'</span><span class="mtag">'+(direct ? '直接執行' : '表單')+'</span>';
      btn.onclick = onclick;
      return btn;
    }};
    const mg = document.createElement("div");
    mg.className = "mgg";
    mg.innerHTML = '<div class="mgghdr">🧠 AI 技能</div>';
    mg.appendChild(makeMobile("查詢AI技能", true, () => {{ closeMob(); doSend("查詢AI技能"); }}));
    mg.appendChild(makeMobile("修改AI技能", false, () => {{ closeMob(); openAISkillModal(); }}));
    mobcont.appendChild(mg);
  }}

  function openAISkillModal() {{
    openModal({{
      title: "修改AI技能",
      fields: [
        {{
          id: "k",
          lbl: "技能 key",
          type: "select",
          req: 1,
          options: skillItems.map(x => ({{ value: x.key, label: x.key + "｜" + (x.label || "") }}))
        }},
        {{
          id: "t",
          lbl: "技能內容",
          type: "textarea",
          req: 1,
          ph: "先預覽目前 skill，再決定要如何修改"
        }}
      ],
      build: function(v) {{
        return "更新AI技能 " + v.k + " | " + v.t;
      }}
    }});

    const keyField = document.getElementById("mf_k");
    const textField = document.getElementById("mf_t");
    const fieldsWrap = document.getElementById("mfields");
    if (!keyField || !textField || !fieldsWrap) return;

    let preview = document.getElementById("ai-skill-preview");
    if (!preview) {{
      preview = document.createElement("div");
      preview.id = "ai-skill-preview";
      preview.style.cssText = "font-size:12px;color:#6c6c70;line-height:1.6;background:#f2f2f7;border-radius:10px;padding:10px;white-space:pre-wrap";
      fieldsWrap.insertBefore(preview, textField.parentElement);
    }}

    async function loadCurrentSkill() {{
      const key = keyField.value;
      preview.textContent = "正在載入目前 AI 技能...";
      try {{
        const r = await fetch("/api/ai-skill/" + encodeURIComponent(key));
        const d = await r.json();
        if (!d.result) {{
          preview.textContent = "查無目前技能內容";
          return;
        }}
        const item = d.result;
        preview.textContent =
          "目前技能預覽\\n" +
          "key: " + key + "\\n" +
          "名稱: " + (item.label || "") + "\\n" +
          "說明: " + (item.description || "") + "\\n\\n" +
          (item.instruction || "");
        textField.value = item.instruction || "";
      }} catch (e) {{
        preview.textContent = "載入目前 AI 技能失敗：" + e.message;
      }}
    }}

    keyField.onchange = loadCurrentSkill;
    loadCurrentSkill();
  }}

  window.openAISkillModal = openAISkillModal;
  if (document.readyState === "loading") {{
    document.addEventListener("DOMContentLoaded", addAISkillButtons);
  }} else {{
    addAISkillButtons();
  }}
}})();
</script>
"""

    inject += """
<script>
(function(){
  async function fetchJson(url){
    try {
      const r = await fetch(url);
      return await r.json();
    } catch (e) {
      return {};
    }
  }

  async function loadTrainingData(){
    const [mods, sessions, partners] = await Promise.all([
      fetchJson('/api/training-modules'),
      fetchJson('/api/training-sessions'),
      fetchJson('/api/partners')
    ]);
    return {
      modules: (mods.result || []).map(x => ({ value: x.title, label: x.title })),
      sessions: (sessions.result || []).map(x => ({ value: x.title, label: x.title })),
      partners: (partners.result || []).map(x => ({ value: x.name, label: x.name }))
    };
  }

  function makeSidebarItem(label, direct, onclick){
    const btn = document.createElement('button');
    btn.className = 'sbtn' + (direct ? ' direct' : ' form-btn');
    btn.innerHTML = '<span class="lbl">' + label + '</span><span class="tag">' + (direct ? '????' : '??') + '</span>';
    btn.onclick = onclick;
    return btn;
  }

  function makeMobileItem(label, direct, onclick){
    const btn = document.createElement('button');
    btn.className = 'mgbtn' + (direct ? ' direct' : ' form-btn');
    btn.innerHTML = '<span class="lbl">' + label + '</span><span class="mtag">' + (direct ? '????' : '??') + '</span>';
    btn.onclick = onclick;
    return btn;
  }

  async function openTrainingForm(kind){
    const data = await loadTrainingData();
    const defs = {
      module_add: {
        title: '??????',
        fields: [
          {id:'title', lbl:'????', type:'text', req:1},
          {id:'kind', lbl:'????', type:'text', req:1},
          {id:'goal', lbl:'????', type:'text', req:1},
          {id:'summary', lbl:'??', type:'textarea'}
        ],
        build: v => `?????? ${v.title} | ${v.kind} | ${v.goal} | ${v.summary || ''}`
      },
      session_add: {
        title: '??????',
        fields: [
          {id:'title', lbl:'????', type:'text', req:1},
          {id:'module', lbl:'????', type:'select', req:1, options:data.modules},
          {id:'date', lbl:'??', type:'text', req:1, ph:'2026-04-10'},
          {id:'time', lbl:'??', type:'text', req:1, ph:'19:30'},
          {id:'location', lbl:'??', type:'text'},
          {id:'teacher', lbl:'??', type:'text'},
          {id:'audience', lbl:'??', type:'text'}
        ],
        build: v => `?????? ${v.title} | ${v.module} | ${v.date} | ${v.time} | ${v.location || ''} | ${v.teacher || ''} | ${v.audience || ''}`
      },
      reflection_add: {
        title: '??????',
        fields: [
          {id:'name', lbl:'??', type:'select', req:1, options:data.partners},
          {id:'session', lbl:'????', type:'select', req:1, options:data.sessions},
          {id:'realize', lbl:'??', type:'textarea', req:1},
          {id:'learn', lbl:'??', type:'textarea', req:1},
          {id:'doit', lbl:'??', type:'textarea', req:1},
          {id:'goal', lbl:'??', type:'textarea', req:1}
        ],
        build: v => `?????? ${v.name} | ${v.session} | ${v.realize} | ${v.learn} | ${v.doit} | ${v.goal}`
      },
      progress_query: {
        title: '??????',
        fields: [{id:'name', lbl:'??', type:'select', req:1, options:data.partners}],
        build: v => `?????? ${v.name}`
      },
      seven_start: {
        title: '??????',
        fields: [
          {id:'name', lbl:'??', type:'select', req:1, options:data.partners},
          {id:'date', lbl:'????', type:'text', req:1, ph:'2026-04-10'},
          {id:'note', lbl:'????', type:'textarea'}
        ],
        build: v => `?????? ${v.name} | ${v.date} | ${v.note || ''}`
      },
      seven_report: {
        title: '??????',
        fields: [
          {id:'name', lbl:'??', type:'select', req:1, options:data.partners},
          {id:'day', lbl:'???', type:'text', req:1, ph:'?1?'},
          {id:'task', lbl:'????', type:'text', req:1},
          {id:'status', lbl:'??', type:'select', req:1, options:[{value:'???',label:'???'},{value:'???',label:'???'}]},
          {id:'note', lbl:'??', type:'textarea'}
        ],
        build: v => `?????? ${v.name} | ${v.day} | ${v.task} | ${v.status} | ${v.note || ''}`
      },
      seven_query: {
        title: '??????',
        fields: [{id:'name', lbl:'??', type:'select', req:1, options:data.partners}],
        build: v => `?????? ${v.name}`
      },
      action_add: {
        title: '??????',
        fields: [
          {id:'name', lbl:'??', type:'select', req:1, options:data.partners},
          {id:'session', lbl:'????', type:'select', req:1, options:data.sessions},
          {id:'action', lbl:'????', type:'textarea', req:1},
          {id:'deadline', lbl:'????', type:'text', req:1, ph:'2026-04-18'}
        ],
        build: v => `?????? ${v.name} | ${v.session} | ${v.action} | ${v.deadline}`
      },
      action_update: {
        title: '??????',
        fields: [
          {id:'name', lbl:'??', type:'select', req:1, options:data.partners},
          {id:'action_id', lbl:'ACTION-ID', type:'text', req:1},
          {id:'status', lbl:'??', type:'text', req:1},
          {id:'note', lbl:'??', type:'textarea'}
        ],
        build: v => `?????? ${v.name} | ${v.action_id} | ${v.status} | ${v.note || ''}`
      },
      action_query: {
        title: '??????',
        fields: [{id:'name', lbl:'??', type:'select', req:1, options:data.partners}],
        build: v => `?????? ${v.name}`
      }
    };
    openModal(defs[kind]);
  }

  function addTrainingButtons(){
    const sidebar = document.getElementById('sidebar');
    const mobcont = document.getElementById('mobcont');
    if (!sidebar || !mobcont || document.getElementById('training-system-clean-group')) return;

    const group = document.createElement('div');
    group.className = 'sg';
    group.id = 'training-system-clean-group';
    group.innerHTML = '<div class="sghdr open"><span>?? ???? 2.0</span><span class="arr">?</span></div><div class="sgitems open"></div>';
    const items = group.querySelector('.sgitems');
    const defs = [
      ['??????', false, () => openTrainingForm('module_add')],
      ['??????', true, () => doSend('??????')],
      ['??????', false, () => openTrainingForm('session_add')],
      ['??????', true, () => doSend('??????')],
      ['??????', false, () => openTrainingForm('reflection_add')],
      ['??????', false, () => openTrainingForm('progress_query')],
      ['??????', true, () => doSend('??????')],
      ['??????', false, () => openTrainingForm('seven_start')],
      ['??????', false, () => openTrainingForm('seven_report')],
      ['??????', false, () => openTrainingForm('seven_query')],
      ['??????', false, () => openTrainingForm('action_add')],
      ['??????', false, () => openTrainingForm('action_update')],
      ['??????', false, () => openTrainingForm('action_query')]
    ];
    defs.forEach(([label, direct, onclick]) => items.appendChild(makeSidebarItem(label, direct, onclick)));
    sidebar.appendChild(group);

    const mg = document.createElement('div');
    mg.className = 'mgg';
    mg.innerHTML = '<div class="mgghdr">?? ???? 2.0</div>';
    defs.forEach(([label, direct, onclick]) => mg.appendChild(makeMobileItem(label, direct, () => { closeMob(); onclick(); })));
    mobcont.appendChild(mg);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addTrainingButtons);
  } else {
    addTrainingButtons();
  }
})();
</script>
"""
    return html.replace("</body>", inject + "\n</body>")
