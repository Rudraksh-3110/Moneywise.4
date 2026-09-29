function toggleSidebar(){
  const sidebar=document.getElementById("sidebar");
  if(sidebar) sidebar.classList.toggle("open");
}
setTimeout(()=>document.querySelectorAll(".flash").forEach(x=>x.remove()),4500);
