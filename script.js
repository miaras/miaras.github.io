// generate a table of contents, adds back button, and a copy button
let divs = document.querySelectorAll('pre div')
let table_of_contents = document.getElementById("table_of_contents");
for (let i = 0; i < divs.length; i++) {
    if (!table_of_contents) {
        break;
    }
    let count = wordCount(divs[i].textContent).toString();
    let entry = document.createElement("a");
    let text = document.createTextNode(divs[i].classList[0] + ", " + divs[i].id + " (" + count + " words)");
    entry.appendChild(text);
    entry.href = "#" + divs[i].id;
    let br = document.createElement("br");
    table_of_contents.appendChild(entry);
    table_of_contents.appendChild(br);
    let back = document.createElement("a");
    let backtext = document.createTextNode("  Back");
    back.appendChild(backtext);
    back.href = "#" + "table_of_contents";
    divs[i].prepend(back);
    let copy = document.createElement("a");
    copy.href = "#";
    copy.textContent = 'Copy';
    console.log(divs[i])
    copy.addEventListener('click', () => {
        event.preventDefault();
        console.log(divs[i])
        copyText(divs[i].id)
    })
    divs[i].prepend(copy);
}

function wordCount(text) {
    let arr = text.split(/\s+/);
    arr = arr.filter(c => c != "");
    return arr.length;
}

function copyText(id) {
    const text = document.getElementById(id);
    navigator.clipboard.writeText(text.innerText.replace("Copy", "").replace("Back", ""))
}

// Language toggle functionality with persistence
function initLanguageToggle() {
    const langToggle = document.getElementById('lang-toggle');
    const englishContent = document.getElementById('english');
    const koreanContent = document.getElementById('korean');

    // Read saved preference; default to English
    let currentLang = localStorage.getItem('preferredLang') || 'en';

    function applyLanguage(lang) {
        // Update content visibility when present on the page
        if (englishContent && koreanContent) {
            if (lang === 'ko') {
                englishContent.classList.add('hidden');
                koreanContent.classList.remove('hidden');
            } else {
                koreanContent.classList.add('hidden');
                englishContent.classList.remove('hidden');
            }
        }
        // Update toggle label when present on the page
        if (langToggle) {
            langToggle.textContent = (lang === 'ko') ? 'English' : '한국어';
        }
    }

    // Initialize UI from saved preference
    applyLanguage(currentLang);

    // Hook up click handler if toggle exists
    if (langToggle) {
        langToggle.addEventListener('click', () => {
            currentLang = (currentLang === 'en') ? 'ko' : 'en';
            localStorage.setItem('preferredLang', currentLang);
            applyLanguage(currentLang);
        });
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLanguageToggle);
} else {
    initLanguageToggle();
}