// ===== Google Script API URL =====
const API_URL = "https://script.google.com/macros/s/AKfycbx6UdvQqj0NABc2ngtTkyzk5dU9CwaMXOIbjUWmMab65A9HqoD387pXY49wHOpBsL-GEg/exec";

async function loadPosts() {
  const container = document.getElementById("messages");
  container.innerHTML = "<p>載入中...</p>";

  try {
    const res = await fetch(API_URL);
    const posts = await res.json();
    renderPosts(posts);
  } catch (err) {
    console.error("讀取貼文失敗:", err);
    container.innerHTML = "<p style='color:red'>讀取失敗，請稍後再試。</p>";
  }
}
import { signOut } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";

document.getElementById("logoutBtn").addEventListener("click", async () => {
  try {
    await signOut(auth);
    window.location.href = "index.html";
  } catch (err) {
    console.error("登出失敗:", err);
  }
});
function renderPosts(posts) {
  const container = document.getElementById("messages");
  container.innerHTML = "";

  if (!posts.length) {
    container.innerHTML = "<p>目前沒有貼文。</p>";
    return;
  }

  posts.reverse().forEach(msg => {
    const div = document.createElement("div");
    div.className = "message";

    const safeContent = String(msg.content).replace(/\n/g, "<br>");

    div.innerHTML = `
      <div class="nickname">${msg.nickname}</div>
      <div class="content">${safeContent}</div>
      <div class="time">${formatTime(msg.time)}</div>
    `;

    container.appendChild(div);
  });
}

function formatTime(isoStr) {
  if (!isoStr) return "";
  const date = new Date(isoStr);
  return date.toLocaleString("zh-TW", { hour12: false });
}

// 頁面載入時自動讀取
document.addEventListener("DOMContentLoaded", loadPosts);