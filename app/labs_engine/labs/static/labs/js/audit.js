/**
 * Galaxy Lab Tool Audit JavaScript
 * Handles audit modal display and highlighting of broken tool containers
 */

// Global variable to store broken tool URLs (set by template)
window.auditBrokenToolUrls = window.auditBrokenToolUrls || [];

$(document).ready(function() {
  // Show audit modal on page load
  $('#auditModal').modal('show');
  
  // Highlight tabs and accordions containing broken tool links
  highlightBrokenToolContainers();
});

/**
 * Highlights tab and accordion containers that contain broken tool links
 */
function highlightBrokenToolContainers() {
  const brokenToolUrls = window.auditBrokenToolUrls;
  
  console.log('Broken tool URLs:', brokenToolUrls);
  
  if (!brokenToolUrls || brokenToolUrls.length === 0) {
    console.log('No broken tools to highlight');
    return; // No broken tools, nothing to highlight
  }
  
  // Function to check if an element contains broken tool links
  function containsBrokenTools(element) {
    const links = element.querySelectorAll('a[href]');
    return Array.from(links).some(link => {
      // Extract tool_id from the link href
      const urlParams = new URLSearchParams(link.search);
      const linkToolId = urlParams.get('tool_id');
      
      if (!linkToolId) return false;
      
      // Check if this tool_id corresponds to any broken tool URL
      return brokenToolUrls.some(brokenUrl => {
        try {
          const brokenUrlParams = new URLSearchParams(new URL(brokenUrl).search);
          const brokenToolId = brokenUrlParams.get('tool_id');
          return linkToolId === brokenToolId;
        } catch (e) {
          console.warn('Error parsing broken URL:', brokenUrl, e);
          return false;
        }
      });
    });
  }
  
  // Highlight tab content containers
  document.querySelectorAll('.tab-content').forEach(tabContent => {
    const tabPanes = tabContent.querySelectorAll('.tab-pane');
    
    tabPanes.forEach(tabPane => {
      if (containsBrokenTools(tabPane)) {
        const tabId = tabPane.id;
        
        // Find corresponding tab button
        const tabButton = document.querySelector(
          `[data-bs-target="#${tabId}"], [href="#${tabId}"]`
        );
        if (tabButton) {
          // Add danger styling to tab button
          tabButton.classList.add('nav-link-danger');
          tabButton.style.borderBottomColor = '#dc3545';
          
          // Add warning icon
          if (!tabButton.querySelector('.fa-exclamation-triangle')) {
            const icon = document.createElement('i');
            icon.className = 'fas fa-exclamation-triangle me-2';
            tabButton.insertBefore(icon, tabButton.firstChild);
          }
          
          console.log(`Highlighted tab: ${tabId}`);
        }
      }
    });
  });
  
  // Highlight accordion items
  document.querySelectorAll('.accordion-item').forEach(accordionItem => {
    const accordionBody = accordionItem.querySelector('.accordion-body');
    
    if (accordionBody && containsBrokenTools(accordionBody)) {
      const accordionButton = accordionItem.querySelector('.accordion-button');
      
      if (accordionButton) {
        // Add danger styling to accordion button
        accordionButton.classList.add('text-danger');
        accordionButton.style.borderColor = '#dc3545';
        
        // Add warning icon
        if (!accordionButton.querySelector('.fa-exclamation-triangle')) {
          const icon = document.createElement('i');
          icon.className = 'fas fa-exclamation-triangle me-2';
          icon.style.color = '#dc3545';
          accordionButton.insertBefore(icon, accordionButton.firstChild);
        }
        
        // Add subtle background color
        accordionButton.style.backgroundColor = '#f8d7da';
        
        const accordionId = accordionButton.getAttribute('aria-controls') ||
                           accordionButton.getAttribute('data-bs-target');
        console.log(`Highlighted accordion: ${accordionId}`);
      }
    }
  });
  
  console.log(`Highlighted containers with ${brokenToolUrls.length} broken tool links`);
}