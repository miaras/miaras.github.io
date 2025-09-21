function collapseSection(element) {
  // get the height of the element's inner content, regardless of its actual size
  var sectionHeight = element.scrollHeight;
  
  // temporarily disable all css transitions
  var elementTransition = element.style.transition;
  element.style.transition = '';
  
  // on the next frame (as soon as the previous style change has taken effect),
  // explicitly set the element's height to its current pixel height, so we 
  // aren't transitioning out of 'auto'
  requestAnimationFrame(function() {
    element.style.height = sectionHeight + 'px';
    element.style.transition = elementTransition;
    
    // on the next frame (as soon as the previous style change has taken effect),
    // have the element transition to height: 0
    requestAnimationFrame(function() {
      element.style.height = 0 + 'px';
    });
  });
  
  // mark the section as "currently collapsed"
  element.setAttribute('data-collapsed', 'true');
}

function collapseSectionImmediate(element) {
    element.style.height = 0 + 'px';
    element.setAttribute('data-collapsed', 'true');
}

function expandSectionImmediate(element) {
    element.style.height = element.scrollHeight + 'px';
    element.setAttribute('data-collapsed', 'false');
}

function expandSection(element) {
  // get the height of the element's inner content, regardless of its actual size
  var sectionHeight = element.scrollHeight;
  
  // have the element transition to the height of its inner content
  element.style.height = sectionHeight + 'px';

  // when the next css transition finishes (which should be the one we just triggered)
  element.addEventListener('transitionend', function(e) {
    // remove this event listener so it only gets triggered once
    element.removeEventListener('transitionend', arguments.callee);
  });
  
  // mark the section as "currently not collapsed"
  element.setAttribute('data-collapsed', 'false');
}

var content_list = document.getElementsByClassName("content");
var j;
for (j = 0; j < content_list.length; j++) {
    collapseSectionImmediate(content_list[j]);
    content_list[j].style.display = "block";
    if (content_list[j] === document.getElementById("intro")) {
        expandSectionImmediate(content_list[j]);
    }
}

var coll = document.getElementsByClassName("collapsible");
var i;

for (i = 0; i < coll.length; i++) {
  coll[i].addEventListener('click', function(e) {
      var content = this.nextElementSibling;
      var isCollapsed = content.getAttribute('data-collapsed') === 'true';
        
      if(isCollapsed) {
        expandSection(content)
        content.setAttribute('data-collapsed', 'false')
      } else {
        collapseSection(content)
      }
    });
}

