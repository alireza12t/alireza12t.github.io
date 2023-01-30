var sections = new Array();

$(document).ready(function () {

    $("#nav-links > a").each(function () {
        sections.push($(this).attr("href").substring(1));
        $(this).click(function (event) {
            event.preventDefault();
            activate($(this));
            smoothScroll($(this.hash));
        })
    });

    $(window).scroll(detectSection);

});

function activate(link) {
    $("#nav-links > a").removeClass("active");
    link.addClass("active");
}

function smoothScroll(destination) {
    $("html,body").animate({scrollTop: destination.position().top - 80}, 500)
}

function detectSection() {
    var currentOffset = $(window).scrollTop();
    for (var i = 0; i < sections.length; i++) {
        var lower = $("#" + sections[i+1]).offset().top - 160;
        if (currentOffset <= lower) {
            activate($("#nav-links > a:eq("+i+")"));
            break;
        }
    }
}