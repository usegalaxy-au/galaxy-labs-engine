// Generic forms logic

$(document).ready(scrollToErrors);

function scrollToErrors() {
    const errors = $('.errorlist');
    if (errors.length) {
      const scrollTo = errors.offset().top - 150;
      $('html, body').animate({scrollTop: scrollTo}, 500);
    }
  }

$('form').submit( () => {
  $('button[type="submit"]').prop('disabled', true);
  $('button[type="submit"]').html('<i class="fas fa-sync-alt fa-spin"></i>');
});
