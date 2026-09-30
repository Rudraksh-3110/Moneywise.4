function toggleSidebar(){
  const sidebar=document.getElementById("sidebar");
  const backdrop=document.getElementById("sidebar-backdrop");
  const button=document.querySelector(".menu-btn");
  if(!sidebar) return;
  const open=sidebar.classList.toggle("open");
  if(backdrop) backdrop.classList.toggle("show",open);
  if(button) button.setAttribute("aria-expanded",open ? "true" : "false");
}
function closeSidebar(){
  const sidebar=document.getElementById("sidebar");
  const backdrop=document.getElementById("sidebar-backdrop");
  const button=document.querySelector(".menu-btn");
  if(sidebar) sidebar.classList.remove("open");
  if(backdrop) backdrop.classList.remove("show");
  if(button) button.setAttribute("aria-expanded","false");
}
document.addEventListener("keydown",event=>{
  if(event.key==="Escape") closeSidebar();
});
document.addEventListener("click",event=>{
  if(event.target.closest("#sidebar a")) closeSidebar();
});
setTimeout(()=>document.querySelectorAll(".flash").forEach(x=>x.remove()),4500);
