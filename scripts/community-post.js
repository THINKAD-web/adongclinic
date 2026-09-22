(function () {
  const params = new URLSearchParams(window.location.search);
  const board = params.get("board");
  const wrId = params.get("wr_id");
  const boardPages = {
    activities: "community-activities.html",
    Press: "community-press.html",
    writing: "community-writing.html",
  };
  const boardTitles = {
    activities: "대외활동",
    Press: "방송 및 보도자료",
    writing: "저술 및 연구활동",
  };

  const titleEl = document.getElementById("postTitle");
  const metaEl = document.getElementById("postMeta");
  const contentEl = document.getElementById("postContent");
  const backEl = document.getElementById("postBack");
  const eyebrowEl = document.getElementById("postEyebrow");

  if (!board || !wrId || !boardPages[board]) {
    titleEl.textContent = "글을 찾을 수 없습니다";
    contentEl.innerHTML = "<p>목록에서 다시 선택해 주세요.</p>";
    backEl.href = "index.html#community";
    return;
  }

  backEl.href = boardPages[board];
  eyebrowEl.textContent = boardTitles[board] || "Archive";
  document.title = boardTitles[board] + " | 한국아동상담센터";

  fetch("data/legacy-board-data.json")
    .then((r) => {
      if (!r.ok) throw new Error("data load failed");
      return r.json();
    })
    .then((data) => {
      const posts = data[board] || [];
      const post = posts.find((p) => String(p.wr_id) === String(wrId));
      if (!post) {
        titleEl.textContent = "글을 찾을 수 없습니다";
        contentEl.innerHTML = "<p>아카이브 데이터에 해당 글이 없습니다.</p>";
        return;
      }
      titleEl.textContent = post.title || "";
      metaEl.textContent = post.list_date ? "등록일 " + post.list_date : "";
      contentEl.innerHTML = post.content_html || "<p>본문이 없습니다.</p>";
      document.title = (post.title || boardTitles[board]) + " | 한국아동상담센터";
    })
    .catch(() => {
      titleEl.textContent = "데이터를 불러오지 못했습니다";
      contentEl.innerHTML = "<p>네트워크 또는 data/legacy-board-data.json 경로를 확인해 주세요.</p>";
    });
})();
