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
