const story = document.getElementById('story');
const chapterNumber = Number(document.body.dataset.chapter);
function addParagraph(section,text){const paragraph=document.createElement('p');paragraph.textContent=text;section.appendChild(paragraph);}
fetch('god-and-cola.txt').then((response)=>{if(!response.ok)throw new Error('Text could not be loaded.');return response.text();}).then((text)=>{
  const lines=text.replace(/^\uFEFF/,'').split(/\r?\n/); const section=document.createElement('section'); let currentChapter; let found=false;
  for(const rawLine of lines){const line=rawLine.trim();if(!line)continue;const chapter=line.match(/^(?:제\s*)?(\d+)화$/);
    if(chapter){const nextChapter=Number(chapter[1]);if(found&&nextChapter!==chapterNumber)break;currentChapter=nextChapter;if(currentChapter===chapterNumber)found=true;continue;}
    if(!found||currentChapter!==chapterNumber)continue;if(line==='***'){const divider=document.createElement('div');divider.className='scene-break';divider.setAttribute('aria-label','장면 전환');divider.textContent='* * *';section.appendChild(divider);}else{addParagraph(section,line);}
  } if(!found)throw new Error('Chapter not found.');story.appendChild(section);
}).catch(()=>{story.innerHTML='<p class="error">본문을 불러오지 못했습니다. <a href="god-and-cola.txt">원문 보기</a></p>';});
