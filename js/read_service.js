import { fetchData } from "./fetch.js";

const postsDiv = document.getElementById("posts");

async function renderPosts() {
  try {
    const rows = await fetchData();
    postsDiv.innerHTML = "";

    rows.forEach(row => {
      const name = row.c[0]?.v ?? "";
      const rawMessage = row.c[1]?.v ?? "";
      const time = row.c[3]?.f ?? row.c[3]?.v ?? "";

      // 確保 message 是字串
      const safeMessage = String(rawMessage);

      // 將 \n 轉成 <br>，讓 HTML 正確換行
      const formattedMessage = safeMessage.replace(/\n/g, "<br>");

      const postDiv = document.createElement("div");
      postDiv.className = "post";
      postDiv.innerHTML = `${name}｜${formattedMessage}｜${time}`; // 使用 innerHTML 支援 <br>

      postsDiv.appendChild(postDiv);
    });
  } catch (err) {
    postsDiv.textContent = "載入失敗";
    console.error("渲染失敗：", err);
  }
}

renderPosts();