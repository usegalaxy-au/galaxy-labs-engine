// Load material icons and display when page has loaded
if ('fonts' in document) {
  document.fonts.ready.then(() => {
    $('.material-icons').css({
      'opacity': 1,
      'max-width': 'unset',
      'overflow': 'visible'
    });
  }).catch((error) => {
    console.error('Font loading failed:', error);
  });
} else {
  // Fallback for browsers that don't support document.fonts
  console.warn('Font API not supported in this browser.');
  $('.material-icons').css({
    'opacity': 1,
    'max-width': 'unset',
    'overflow': 'visible'
  });
}
