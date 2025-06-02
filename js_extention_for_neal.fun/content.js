
function openItemsStore(retries = 5, delay = 1000) {
  return new Promise((resolve, reject) => {
    const attempt = (count) => {
      const openReq = indexedDB.open("infinite-craft");

      openReq.onsuccess = () => {
        const db = openReq.result;
        if (db.objectStoreNames.contains("items")) {
          const tx = db.transaction("items", "readwrite");
          const store = tx.objectStore("items");
          resolve({ db, store, tx });
        } else if (count > 0) {
          console.warn("⏳ Waiting for 'items' store...");
          setTimeout(() => attempt(count - 1), delay);
        } else {
          reject("❌ 'items' store not found after retries.");
        }
      };

      openReq.onerror = () => {
        reject("❌ Failed to open IndexedDB.");
      };
    };

    attempt(retries);
  });
}

async function mergeElements(first, second) {
  try {
    const res = await fetch(`https://neal.fun/api/infinite-craft/pair?first=${encodeURIComponent(first)}&second=${encodeURIComponent(second)}`, {
      method: "GET",
      headers: {
        "Accept": "*/*",
        "User-Agent": navigator.userAgent,
        "Referer": "https://neal.fun/infinite-craft/",
        "Origin": "https://neal.fun"
      }
    });

    const data = await res.json();
    console.log(`🧪 Merge result for ${first} + ${second}:`, data);
    return data;

  } catch (err) {
    console.error("❌ Merge request failed:", err);
    return null;
  }
}

async function checkForCommands() {
  try {
    const res = await fetch("http://127.0.0.1:5000/get_command");
    const command = await res.json();

    if (command.status === "no_command") {
      console.warn("⚠️ No command to process");
      return;
    }

    if (command.action === "ADD_ITEM") {
        const item = command.data;

        if (typeof item.saveId !== "number") {
            console.error("❌ item.saveId is missing or invalid:", item);
            return;
        }

        openItemsStore().then(({ store }) => {
            store.getAllKeys().onsuccess = function (e) {
            const keys = e.target.result.filter(k => k[0] === item.saveId);
            const nextIndex = keys.length > 0
                ? Math.max(...keys.map(k => k[1])) + 1
                : 0;

            item.id = nextIndex;
            store.put(item);
            console.log(`✅ Added from Python → key: [${item.saveId}, ${nextIndex}]`, item);
            };
        }).catch(console.error);
        }

    else if (command.action === "MERGE") {
        const { first, second, saveId = 0 } = command.data;

        const result = await mergeElements(first, second);
        if (!result || !result.result) {
            console.warn("⚠️ Merge failed or no result returned");
            return;
        }

        const item = {
            id: null,  // Let Python decide ID if needed
            saveId: saveId,
            text: result.result,
            emoji: result.emoji,
            isNew: result.isNew,
            recipes: [[first, second]]
        };

        // Send merged result to Python
        fetch("http://127.0.0.1:5000/merged_result", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(item)
        }).then(() => {
            console.log("📤 Sent merged result to Python:", item);
        }).catch(err => {
            console.error("❌ Failed to send merged result to Python:", err);
        });

        console.log(`🧪 Merged [${first} + ${second}] →`, item);
    }



  } catch (err) {
    console.error("❌ Command fetch error:", err);
  }
}


// Run command checker every 5s
async function loopCommands() {
  while (true) {
    await checkForCommands();
    await new Promise(r => setTimeout(r, 5));  // 500ms delay between loops
  }
}
loopCommands();
// Optional: run fetch & send once on load
