(function(C,A,L){var p=function(a,ar){a.q.push(ar)};var d=C.document;C.Cal=C.Cal||function(){var cal=C.Cal;var ar=arguments;if(!cal.loaded){cal.ns={};cal.q=cal.q||[];d.head.appendChild(d.createElement("script")).src=A;cal.loaded=true}if(ar[0]===L){var api=function(){p(api,arguments)};var namespace=ar[1];api.q=api.q||[];if(typeof namespace==="string"){cal.ns[namespace]=cal.ns[namespace]||api;p(cal.ns[namespace],ar);p(cal,["initNamespace",namespace])}else p(cal,ar);return}p(cal,ar)}})(window,"https://app.cal.com/embed/embed.js","init");
(function(){
  Cal("init",{origin:"https://cal.com"});
  Cal("ui",{styles:{branding:{brandColor:"#35507A"}},hideEventTypeDetails:false,layout:"month_view"});
  var sc=document.querySelector('script[src="https://app.cal.com/embed/embed.js"]'),ready=false;
  if(sc){sc.addEventListener('load',function(){ready=true});sc.addEventListener('error',function(){ready=false})}
  document.addEventListener('click',function(e){
    var a=e.target.closest&&e.target.closest('a[href^="https://cal.com/millwright-data"]');
    if(!a||!ready||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;
    e.preventDefault();
    Cal("modal",{calLink:a.getAttribute('href').replace('https://cal.com/','')});
  });
})();
(function(){
  var flags=[].slice.call(document.querySelectorAll('.hdr-flag'));if(!flags.length)return;
  function closeAll(except){flags.forEach(function(f){if(f!==except)f.classList.remove('is-open')})}
  flags.forEach(function(f){
    f.addEventListener('click',function(e){e.preventDefault();var on=f.classList.contains('is-open');closeAll();if(!on)f.classList.add('is-open')});
  });
  document.addEventListener('click',function(e){if(!e.target.closest||!e.target.closest('.hdr-flag'))closeAll()});
  document.addEventListener('keydown',function(e){if(e.key==='Escape')closeAll()});
})();
(function(){
  var els=[].slice.call(document.querySelectorAll('.rv'));if(!els.length)return;
  if(!('IntersectionObserver' in window)){els.forEach(function(e){e.classList.add('in')});return}
  var io=new IntersectionObserver(function(entries){
    entries.forEach(function(en){if(en.isIntersecting){en.target.classList.add('in');io.unobserve(en.target)}});
  },{rootMargin:'0px 0px -10% 0px',threshold:0.08});
  els.forEach(function(e){io.observe(e)});
})();
(function(){
  var btn=document.querySelector('.menu-btn'),nav=document.getElementById('site-nav');
  if(!btn||!nav)return;
  function set(open){btn.setAttribute('aria-expanded',open?'true':'false');document.documentElement.classList.toggle('menu-open',open)}
  btn.addEventListener('click',function(){set(btn.getAttribute('aria-expanded')!=='true')});
  nav.addEventListener('click',function(e){if(e.target.closest('a'))set(false)});
  document.addEventListener('keydown',function(e){if(e.key==='Escape')set(false)});
})();
