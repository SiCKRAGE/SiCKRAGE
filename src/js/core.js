import 'bootstrap';
import 'bootstrap-formhelpers/dist/js/bootstrap-formhelpers';
import 'tablesorter';
import 'tablesorter/dist/js/widgets/widget-columnSelector.min';
import 'tooltipster';
import 'timeago';
import 'jquery-form';
import 'jquery-backstretch';
import 'jquery-ui/ui/disable-selection';
import 'jquery-ui/ui/widgets/slider';
import 'jquery-ui/ui/widgets/sortable';
import 'jquery-ui/ui/widgets/dialog';
import 'jquery-ui/ui/widgets/autocomplete';
import 'pnotify/dist/es/PNotifyMobile';
import 'pnotify/dist/es/PNotifyButtons';
import 'pnotify/dist/es/PNotifyDesktop';
import {addLocale, gettext, useLocale} from 'ttag';
import {po} from 'gettext-parser'
import jconfirm from 'jquery-confirm';
import PNotify from 'pnotify/dist/es/PNotify';
import jQueryBridget from 'jquery-bridget';
import Isotope from 'isotope-layout';
import ImagesLoaded from 'imagesloaded';
import Tokenfield from 'tokenfield';
import _ from 'underscore';
import * as Sentry from '@sentry/browser';

Sentry.init({
    dsn: process.env.SENTRY_DSN,
    release: process.env.PACKAGE_VERSION,
    beforeSend(event, hint) {
        if (event.exception) {
            event.exception.values[0].stacktrace.frames.forEach((frame) => {
                frame.filename = frame.filename.substring(frame.filename.lastIndexOf("/"))
            });
        }
        return event;
    }
});

jQueryBridget('isotope', Isotope, $);
jQueryBridget('imagesLoaded', ImagesLoaded, $);

var gt = function (msgid) {
    return gettext(msgid);
};

$(document).ready(function ($) {
    var SICKRAGE = {
        ws_notifications: function () {
            const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            var ws = new WebSocket(proto + '//' + window.location.hostname + ':' + window.location.port + SICKRAGE.srWebRoot + '/ws/ui');

            ws.onmessage = function (evt) {
                var msg = $.parseJSON(evt.data);

                switch (msg.type) {
                    case 'notification':
                        SICKRAGE.notify(msg.data.type, msg.data.title, msg.data.body);
                        break;
                    case 'redirect':
                        window.location.href = msg.data.url;
                        break;
                }
            };
        },

        text_viewer: function () {
            var minimized_elements = $('p.text-viewer');

            minimized_elements.each(function () {
                var t = $(this).text();
                if (t.length < 500) return;

                $(this).html(
                    t.slice(0, 500) + '<span>... </span><a href="#" class="read-more"> Read More</a>' +
                    '<span style="display:none;">' + t.slice(500, t.length) + ' <a href="#" class="read-less"> Read Less </a></span>'
                );
            });

            $('a.read-more', minimized_elements).click(function (event) {
                event.preventDefault();
                $(this).hide().prev().hide();
                $(this).next().show();
            });

            $('a.read-less', minimized_elements).click(function (event) {
                event.preventDefault();
                $(this).parent().hide().prev().show().prev().show();
            });
        },

        notify: function (type, title, message) {
            PNotify.modules.Desktop.permission();
            new PNotify({
                stack: {'dir1': 'up', 'dir2': 'left', 'firstpos1': 25, 'firstpos2': 25},
                icons: 'fontawesome5',
                styling: 'bootstrap4',
                addclass: "stack-bottomright",
                delay: 5000,
                hide: true,
                history: false,
                shadow: false,
                width: '340px',
                target: document.body,
                data: {
                    modules: {
                        Desktop: {
                            desktop: true,
                            icon: SICKRAGE.srWebRoot + '/images/logo-badge.png'
                        }
                    },
                    type: type,
                    title: title,
                    text: message.replace(/<br[\s/]*(?:\s[^>]*)?>/ig, "\n")
                        .replace(/<[/]?b(?:\s[^>]*)?>/ig, '*')
                        .replace(/<i(?:\s[^>]*)?>/ig, '[').replace(/<[/]i>/ig, ']')
                        .replace(/<(?:[/]?ul|\/li)(?:\s[^>]*)?>/ig, '').replace(/<li(?:\s[^>]*)?>/ig, "\n" + '* ')
                }
            });
        },

        isMeta: function (pyVar, result) {
            var reg = new RegExp(result.length > 1 ? result.join('|') : result);
            return (reg).test($('meta[data-var="' + pyVar + '"]').data('content'));
        },

        getMeta: function (pyVar) {
            return $('meta[data-var="' + pyVar + '"]').data('content');
        },

        metaToBool: function (pyVar) {
            var meta = $('meta[data-var="' + pyVar + '"]').data('content');
            if (meta === undefined) {
                return meta;
            } else {
                meta = (isNaN(meta) ? meta.toLowerCase() : meta.toString());
                return !(meta === 'false' || meta === 'none' || meta === '0');
            }
        },

        popupWindow: function (myURL, title, myWidth, myHeight) {
            const left = (screen.width - myWidth) / 2;
            const top = (screen.height - myHeight) / 4;
            return window.open(myURL, title, 'toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=no, resizable=no, copyhistory=no, width=' + myWidth + ', height=' + myHeight + ', top=' + top + ', left=' + left);
        },

        showHideRows: function (whichClass, status) {
            $("tr." + whichClass).each(function () {
                if (status) {
                    $(this).show();
                } else {
                    $(this).hide();
                }
            });
        },

        updateUrlParameter: function (uri, key, value) {
            // remove the hash part before operating on the uri
            var i = uri.indexOf('#');
            var hash = i === -1 ? '' : uri.substr(i);
            uri = i === -1 ? uri : uri.substr(0, i);

            var re = new RegExp("([?&])" + key + "=.*?(&|$)", "i");
            var separator = uri.indexOf('?') !== -1 ? "&" : "?";

            if (!value) {
                // remove key-value pair if value is empty
                uri = uri.replace(new RegExp("([?&]?)" + key + "=[^&]*", "i"), '');
                if (uri.slice(-1) === '?') {
                    uri = uri.slice(0, -1);
                }

                // replace first occurrence of & by ? if no ? is present
                if (uri.indexOf('?') === -1) {
                    uri = uri.replace(/&/, '?');
                }
            } else if (uri.match(re)) {
                uri = uri.replace(re, '$1' + key + "=" + value + '$2');
            } else {
                uri = uri + separator + key + "=" + value;
            }
            return uri + hash;
        },

        quicksearch: function () {
            $.widget("custom.catcomplete", $.ui.autocomplete, {
                _create: function () {
                    this._super();
                    this.widget().menu("option", "items", "> :not(.ui-autocomplete-category)");
                },
                _renderMenu: function (ul, items) {
                    var that = this,
                        currentCategory = "";
                    $.each(items, function (index, item) {
                        var li;
                        if (item.category != currentCategory) {
                            ul.append("<li class='ui-autocomplete-category text-warning p-1'><strong class='text-uppercase'>" + item.category + "</strong></li>");
                            currentCategory = item.category;
                        }
                        li = that._renderItemData(ul, item);
                        if (item.category) {
                            li.attr("aria-label", item.category + " : " + item.name);
                        }
                    });
                },
                _renderItem: function (ul, item) {
                    var $li = $('<li class="bg-transparent m-1">'),
                        $img = $('<img>'),
                        $a = $('<a>');

                    $li.attr('data-value', item.name);

                    $img.attr({
                        src: item.img,
                        alt: item.name,
                        class: 'img-fluid w-100'
                    });

                    if (item.category === 'shows') {
                        if (item.showid) {
                            $a.attr({
                                href: `${SICKRAGE.srWebRoot}/home/displayShow?show=${item.showid}`,
                                class: 'btn btn-dark btn-block d-inline-block text-left'
                            });
                        } else {
                            $a.attr({
                                href: `${SICKRAGE.srWebRoot}/home/addShows/newShow?search_string=${item.name}`,
                                class: 'btn btn-dark btn-block d-inline-block text-left'
                            });
                        }

                        $li.append($a);
                        $li.find('a').append($('<div class="row"><div class="col-2"><div id="show-img"></div></div><div class="col-10"><div class="row"><strong id="show-name" class="text-white text-truncate"></strong></div><div class="row"><strong id="show-seasons" class="text-secondary"></strong></div></div></div>'));
                        $li.find('#show-img').append($img);

                        if (item.showid) {
                            $li.find('#show-name').append(item.name);
                        } else {
                            $li.find('#show-name').append('Add new show: ' + item.name);
                        }

                        $li.find('#show-seasons').append(item.seasons + ' seasons');
                    } else {
                        $a.attr({
                            href: `${SICKRAGE.srWebRoot}/home/displayShow?show=${item.showid}#S${item.season}E${item.episode}`,
                            class: 'btn btn-dark btn-block d-inline-block text-left'
                        });

                        $li.append($a);
                        $li.find('a').append($('<div class="row"><div class="col-2"><div id="show-img"></div></div><div class="col-10"><div class="row"><strong id="ep-name" class="text-white"></strong></div><div class="row"><strong id="show-name" class="text-secondary text-truncate"></strong></div></div></div>'));
                        $li.find('#show-img').append($img);
                        $li.find('#ep-name').append(item.name);
                        $li.find('#show-name').append(item.showname);
                    }

                    return $li.appendTo(ul);
                }
            });

            $('#quicksearch').catcomplete({
                delay: 1000,
                minLength: 1,
                source: function (request, response) {
                    $.ajax({
                        url: `${SICKRAGE.srWebRoot}/quicksearch.json`,
                        dataType: "json",
                        type: "POST",
                        data: {term: request.term},
                        success: function (data) {
                            response(data);
                        }
                    })
                },
                // search: function () {
                //     $("#quicksearch-icon").addClass('fas fa-spinner fa-spin');
                // },
                focus: function (event, ui) {
                    $('#quicksearch').val(ui.item.name);
                    return false;
                },
                open: function () {
                    $(".quicksearch-input-container").append('<button type="button" class="quicksearch-input-btn"><i class="fas fa-1x fa-times-circle text-white m-2" aria-hidden="true"></i></button>');
                    $("ul.ui-menu").width($(this).innerWidth());
                    $("ul.ui-menu").css('border', 'none');
                    $("ul.ui-menu").css('outline', 'none');
                    $("ul.ui-menu").addClass('bg-dark shadow rounded');
                    $(".quicksearch-input-btn").click(function () {
                        $('#quicksearch').catcomplete('close').val('');
                        $(this).remove();
                    });
                }
            });
        },

        updateProfileBadge: function () {
            let total_count = 0;

            $.getJSON(SICKRAGE.srWebRoot + "/logs/errorCount", function (data) {
                if (data.count) {
                    total_count += data.count;
                    $('#numErrors').text(data.count);
                    $('#numErrors').parent().removeClass('d-none');
                } else {
                    $('#numErrors').parent().addClass('d-none');
                }

                if (total_count) {
                    $('#profile-badge').text(total_count);
                } else {
                    $('#profile-badge').text('');
                }
            });

            $.getJSON(SICKRAGE.srWebRoot + "/logs/warningCount", function (data) {
                if (data.count) {
                    total_count += data.count;
                    $('#numWarnings').text(data.count);
                    $('#numWarnings').parent().removeClass('d-none');
                } else {
                    $('#numWarnings').parent().addClass('d-none');
                }

                if (total_count) {
                    $('#profile-badge').text(total_count);
                } else {
                    $('#profile-badge').text('');
                }
            });

            $.getJSON(SICKRAGE.srWebRoot + "/announcements/announcementCount", function (data) {
                if (data.count) {
                    total_count += data.count;
                    $('#numAnnouncements').text(data.count);
                } else {
                    $('#numAnnouncements').text('');
                }

                if (total_count) {
                    $('#profile-badge').text(total_count);
                } else {
                    $('#profile-badge').text('');
                }
            });
        },

        common: {
            init: function () {
                SICKRAGE.srPID = SICKRAGE.getMeta('srPID');
                SICKRAGE.srWebRoot = SICKRAGE.getMeta('srWebRoot');
                SICKRAGE.srDefaultPage = SICKRAGE.getMeta('srDefaultPage');
                SICKRAGE.loadingHTML = '<i class="fas fa-spinner fa-spin fa-fw"></i>';
                SICKRAGE.anonURL = SICKRAGE.getMeta('anonURL');

                SICKRAGE.ws_notifications();
                SICKRAGE.updateProfileBadge();

                // add locale translation
                $.get(`${SICKRAGE.srWebRoot}/messages.po`, function (data) {
                    if (data) {
                        addLocale(SICKRAGE.getMeta('srLocale'), po.parse(data));
                        useLocale(SICKRAGE.getMeta('srLocale'));
                    }
                });

                // init quicksearch
                SICKRAGE.quicksearch();

                $(window).scroll(function () {
                    if ($(this).scrollTop() > 50) {
                        $('#back-to-top').fadeIn();
                    } else {
                        $('#back-to-top').fadeOut();
                    }
                });

                // scroll body to 0px on click
                $('#back-to-top').click(function () {
                    $('body,html').animate({
                        scrollTop: 0
                    }, 800);
                    return false;
                });

                // tooltips
                $('[title!=""]').tooltipster();

                var imgDefer = document.getElementsByTagName('img');
                for (var i = 0; i < imgDefer.length; i++) {
                    if (imgDefer[i].getAttribute('data-src')) {
                        imgDefer[i].setAttribute('src', imgDefer[i].getAttribute('data-src'));
                    }
                }

                // hack alert: if we don't have a touchscreen, and we are already hovering the mouse, then click should link instead of toggle
                if ((navigator.maxTouchPoints || 0) < 2) {
                    $('.dropdown-toggle').on('click', function () {
                        if ($(this).attr('aria-expanded') === 'true') {
                            window.location.href = $(this).attr('href');
                        }
                    });
                }

                if (SICKRAGE.metaToBool('sickrage.FUZZY_DATING')) {
                    $.timeago.settings.allowFuture = true;
                    $.timeago.settings.strings = {
                        prefixAgo: null,
                        prefixFromNow: 'In ',
                        suffixAgo: "ago",
                        suffixFromNow: "",
                        seconds: "less than a minute",
                        minute: "about a minute",
                        minutes: "%d minutes",
                        hour: "an hour",
                        hours: "%d hours",
                        day: "a day",
                        days: "%d days",
                        month: "a month",
                        months: "%d months",
                        year: "a year",
                        years: "%d years",
                        wordSeparator: " ",
                        numbers: []
                    };
                    $("[datetime]").timeago();
                }

                $.tablesorter.addParser(
                    {
                        id: 'loadingNames',
                        is: function () {
                            return false;
                        },
                        format: function (s) {
                            if (0 === s.indexOf('Loading...')) {
                                return s.replace('Loading...', '000');
                            } else {
                                return (SICKRAGE.metaToBool('sickrage.SORT_ARTICLE') ? (s || '') : (s || '').replace(/^(The|A|An)\s/i, ''));
                            }
                        },
                        type: 'text'
                    }
                );

                $.tablesorter.addParser(
                    {
                        id: 'quality',
                        is: function () {
                            return false;
                        },
                        format: function (s) {
                            return s.replace('hd1080p', 5).replace('hd720p', 4).replace('hd', 3).replace('sd', 2).replace('any', 1).replace('best', 0).replace('custom', 7);
                        },
                        type: 'numeric'
                    }
                );

                $.tablesorter.addParser(
                    {
                        id: 'realISODate',
                        is: function () {
                            return false;
                        },
                        format: function (s) {
                            return new Date(s).getTime();
                        },
                        type: 'numeric'
                    }
                );

                $.tablesorter.addParser(
                    {
                        id: 'cDate',
                        is: function () {
                            return false;
                        },
                        format: function (s) {
                            return s;
                        },
                        type: 'numeric'
                    }
                );

                $.tablesorter.addParser(
                    {
                        id: 'eps',
                        is: function () {
                            return false;
                        },
                        format: function (s) {
                            var match = s.match(/^(.*)/);

                            if (match === null || match[1] === "?") {
                                return -10;
                            }

                            var nums = match[1].split(" / ");
                            if (nums[0].indexOf("+") !== -1) {
                                var numParts = nums[0].split("+");
                                nums[0] = numParts[0];
                            }

                            nums[0] = parseInt(nums[0]);
                            nums[1] = parseInt(nums[1]);

                            if (nums[0] === 0) {
                                return nums[1];
                            }
                            var finalNum = parseInt((SICKRAGE.getMeta('max_download_count')) * nums[0] / nums[1]);
                            var pct = Math.round((nums[0] / nums[1]) * 100) / 1000;
                            if (finalNum > 0) {
                                finalNum += nums[0];
                            }

                            return finalNum + pct;
                        },
                        type: 'numeric'
                    }
                );

                jconfirm.defaults = {
                    theme: 'dark',
                    type: 'blue',
                    typeAnimated: true,
                    confirm: function () {
                        location.href = this.$target.attr('href');
                    }
                };

                $('a.shutdown').confirm({
                    theme: 'dark',
                    title: gt('Shutdown'),
                    content: gt('Are you sure you want to shutdown SiCKRAGE ?')
                });

                $('a.restart').confirm({
                    theme: 'dark',
                    title: gt('Restart'),
                    content: gt('Are you sure you want to restart SiCKRAGE ?')
                });

                $('a.submiterrors').confirm({
                    theme: 'dark',
                    title: gt('Submit Errors'),
                    content: gt('Are you sure you want to submit these errors ?') + '<br><br><span class="text-danger">' + gt('Make sure SiCKRAGE is updated and trigger') + '<br>' + gt('this error with debug enabled before submitting') + '</span>'
                });

                $('#removeW').click(function () {
                    !$('#white option:selected').remove().appendTo('#pool');
                });

                $('#addW').click(function () {
                    !$('#pool option:selected').remove().appendTo('#white');
                });

                $('#addB').click(function () {
                    !$('#pool option:selected').remove().appendTo('#black');
                });

                $('#removeP').click(function () {
                    !$('#pool option:selected').remove();
                });

                $('#removeB').click(function () {
                    !$('#black option:selected').remove().appendTo('#pool');
                });

                $('#addToWhite').click(function () {
                    var group = $('#addToPoolText').val();
                    if (group !== '') {
                        var option = $('<option>');
                        option.attr('value', group);
                        option.html(group);
                        option.appendTo('#white');
                        $('#addToPoolText').val('');
                    }
                });

                $('#addToBlack').click(function () {
                    var group = $('#addToPoolText').val();
                    if (group !== '') {
                        var option = $('<option>');
                        option.attr('value', group);
                        option.html(group);
                        option.appendTo('#black');
                        $('#addToPoolText').val('');
                    }
                });

                $("input:checkbox.enabler").each(function () {
                    if (!$(this).prop('checked')) {
                        $('#content_' + $(this).attr('id')).hide();
                    } else {
                        $('#content_' + $(this).attr('id')).show();
                    }
                });

                $("input:checkbox.enabler").on('click', function () {
                    if ($(this).prop('checked')) {
                        $('#content_' + $(this).attr('id')).fadeIn("fast", "linear");
                    } else {
                        $('#content_' + $(this).attr('id')).fadeOut("fast", "linear");
                    }
                });

                $('.modal').on('shown.bs.modal', function () {
                    $('body').addClass('modal-open');
                    $('body').removeAttr('style');
                });

                SICKRAGE.browser.init();
                SICKRAGE.quality_chooser.init();

                $("#changelog").on('click', function (event) {
                    event.preventDefault();
                    $("#changelogModal").find('.modal-body').load(SICKRAGE.srWebRoot + '/changelog');
                    $("#changelogModal").modal();
                });

                SICKRAGE.text_viewer();
            }
        },

        ajax_search: {
            searchStatusUrl: '/home/getManualSearchStatus',
            failedDownload: false,
            qualityDownload: false,
            selectedEpisode: '',
            manualSearches: [],

            init: function () {
                //PNotify.prototype.options.maxonscreen = 5;

                SICKRAGE.ajax_search.searchStatusUrl = SICKRAGE.srWebRoot + SICKRAGE.ajax_search.searchStatusUrl;
                SICKRAGE.ajax_search.ajaxEpSearch({'colorRow': true});
                SICKRAGE.ajax_search.checkManualSearches();
                SICKRAGE.ajax_search.ajaxEpSubtitlesSearch();
            },

            enableLink: function (el) {
                el.on('click.disabled', false);
                el.prop('enableClick', '1');
                el.fadeTo("fast", 1);
            },

            disableLink: function (el) {
                el.off('click.disabled');
                el.prop('enableClick', '0');
                el.fadeTo("fast", 0.5);
            },

            updateImages: function (data) {
                $.each(data.episodes, function (name, ep) {
                    var loadingIcon = 'fas fa-spinner fa-spin fa-fw';
                    var queuedIcon = 'fas fa-clock';
                    var searchIcon = 'fas fa-search';
                    var htmlContent = '';
                    var el = $('a[id=' + ep.show + 'x' + ep.season + 'x' + ep.episode + ']');
                    var img = el.children('i');
                    var parent = el.parent();

                    if (el) {
                        var rSearchTerm = '';
                        if (ep.searchstatus.toLowerCase() === 'searching') {
                            img.prop('title', gt('Searching'));
                            img.prop('class', loadingIcon);
                            SICKRAGE.ajax_search.disableLink(el);
                            htmlContent = ep.searchstatus;

                        } else if (ep.searchstatus.toLowerCase() === 'queued') {
                            img.prop('title', gt('Queued'));
                            img.prop('class', queuedIcon);
                            SICKRAGE.ajax_search.disableLink(el);
                            htmlContent = ep.searchstatus;
                        } else if (ep.searchstatus.toLowerCase() === 'finished') {
                            img.prop('title', gt('Searching'));
                            img.parent().prop('class', 'epRetry');
                            img.prop('class', searchIcon);
                            SICKRAGE.ajax_search.enableLink(el);

                            // Update Status and Quality
                            rSearchTerm = /(\w+)\s\((.+?)\)/;
                            htmlContent = ep.status.replace(rSearchTerm, "$1" + ' <span class="badge text-white ' + ep.quality + '">' + "$2" + '</span>');
                            parent.closest('tr').prop("class", ep.overview + " season-" + ep.season + " seasonstyle font-weight-bold text-dark");
                        }
                        // update the status column if it exists
                        parent.siblings('.col-status').html(htmlContent);

                    }

                    var elementCompleteEpisodes = $('a[id=forceUpdate-' + ep.show + 'x' + ep.season + 'x' + ep.episode + ']');
                    var imageCompleteEpisodes = elementCompleteEpisodes.children('i');
                    if (elementCompleteEpisodes) {
                        if (ep.searchstatus.toLowerCase() === 'searching') {
                            imageCompleteEpisodes.prop('title', gt('Searching'));
                            imageCompleteEpisodes.prop('alt', 'searching');
                            imageCompleteEpisodes.prop('class', loadingIcon);
                            SICKRAGE.ajax_search.disableLink(elementCompleteEpisodes);
                        } else if (ep.searchstatus.toLowerCase() === 'queued') {
                            imageCompleteEpisodes.prop('title', gt('Queued'));
                            imageCompleteEpisodes.prop('alt', 'queued');
                            imageCompleteEpisodes.prop('class', queuedIcon);
                        } else if (ep.searchstatus.toLowerCase() === 'finished') {
                            imageCompleteEpisodes.prop('title', gt('Manual Search'));
                            imageCompleteEpisodes.prop('alt', '[search]');
                            imageCompleteEpisodes.prop('class', searchIcon);
                            if (ep.overview.toLowerCase() === 'snatched') {
                                elementCompleteEpisodes.closest('tr').remove();
                            } else {
                                SICKRAGE.ajax_search.enableLink(elementCompleteEpisodes);
                            }
                        }
                    }
                });
            },

            manualSearch: function (options) {
                var imageName, imageResult, htmlContent;

                var parent = SICKRAGE.ajax_search.selectedEpisode.parent();

                // Create var for anchor
                var link = SICKRAGE.ajax_search.selectedEpisode;

                // Create var for img under anchor and set options for the loading gif
                var img = SICKRAGE.ajax_search.selectedEpisode.children('i');
                img.prop('title', gt('loading'));
                img.prop('class', options.loadingIcon);

                var url = SICKRAGE.ajax_search.selectedEpisode.prop('href');

                if (SICKRAGE.ajax_search.failedDownload === false) {
                    url = url.replace("retryEpisode", "searchEpisode");
                }

                url = url + "&downCurQuality=" + (SICKRAGE.ajax_search.qualityDownload ? '1' : '0');

                $.getJSON(url, function (data) {
                    // if they failed then just put the red X
                    if (data.result.toLowerCase() === 'failure') {
                        imageName = options.noIcon;
                        imageResult = 'failed';

                        // if the snatch was successful then apply the corresponding class and fill in the row appropriately
                    } else {
                        imageName = options.loadingIcon;
                        imageResult = 'success';
                        // color the row
                        if (options.colorRow) {
                            parent.parent().removeClass('skipped wanted qual good unaired').addClass('snatched');
                        }
                        // applying the quality class
                        var rSearchTerm = /(\w+)\s\((.+?)\)/;
                        htmlContent = data.result.replace(rSearchTerm, "$1" + ' <span class="badge text-white ' + data.quality + '">' + "$2" + '</span>');
                        // update the status column if it exists
                        parent.siblings('.col-status').html(htmlContent);
                        // Only if the queuing was successful, disable the onClick event of the loading image
                        SICKRAGE.ajax_search.disableLink(link);
                    }

                    // put the corresponding image as the result of queuing of the manual search
                    img.prop('title', imageResult);
                    img.prop('height', options.size);
                    img.prop('class', imageName);
                });

                // don't follow the link
                return false;
            },

            checkManualSearches: function () {
                const showId = $('#showID').val();

                if (showId !== undefined) {
                    let pollInterval = 5000;

                    $.ajax({
                        url: SICKRAGE.ajax_search.searchStatusUrl + `?show=${showId}`,
                        success: function (data) {
                            if (data.episodes) {
                                pollInterval = 5000;
                            } else {
                                pollInterval = 15000;
                            }

                            SICKRAGE.ajax_search.updateImages(data);
                            //cleanupManualSearches(data);
                        },
                        error: function () {
                            pollInterval = 30000;
                        },
                        type: "GET",
                        dataType: "json",
                        complete: function () {
                            setTimeout(SICKRAGE.ajax_search.checkManualSearches, pollInterval);
                        },
                        timeout: 15000 // timeout every 15 secs
                    });
                }
            },

            ajaxEpSearch: function (options) {
                var defaults = {
                    size: 16,
                    colorRow: false,
                    loadingIcon: 'fas fa-spinner fa-spin fa-fw',
                    queuedIcon: 'fas fa-clock',
                    noIcon: 'fas fa-times',
                    yesIcon: 'fas fa-check'
                };

                options = $.extend({}, defaults, options);

                $('.epRetry').click(function (event) {
                    event.preventDefault();

                    // Check if we have disabled the click
                    if ($(this).prop('enableClick') === '0') {
                        return false;
                    }

                    SICKRAGE.ajax_search.selectedEpisode = $(this);

                    $("#manualSearchModalFailed").modal();
                });

                $('.epSearch').click(function (event) {
                    event.preventDefault();

                    // Check if we have disabled the click
                    if ($(this).prop('enableClick') === '0') {
                        return false;
                    }

                    SICKRAGE.ajax_search.selectedEpisode = $(this);

                    if ($(this).parent().parent().children(".col-status").children(".quality").length) {
                        $("#manualSearchModalQuality").modal();
                    } else {
                        SICKRAGE.ajax_search.manualSearch(options);
                    }
                });

                $('#manualSearchModalFailed .btn').click(function () {
                    SICKRAGE.ajax_search.failedDownload = (this.classList.contains('btn-success'));
                });

                $('#manualSearchModalQuality .btn').click(function () {
                    SICKRAGE.ajax_search.qualityDownload = (this.classList.contains('btn-success'));
                    SICKRAGE.ajax_search.manualSearch(options);
                });
            },

            ajaxEpSubtitlesSearch: function () {
                $('.epSubtitlesSearch').click(function () {
                    var subtitlesTd = $(this).parent().siblings('.col-subtitles');
                    var subtitlesSearchLink = $(this);
                    // fill with the ajax loading gif
                    subtitlesSearchLink.empty();
                    subtitlesSearchLink.append($("<i/>").attr({
                        "class": "fas fa-spinner fa-spin fa-fw",
                        "title": gt("loading")
                    }));
                    $.getJSON($(this).attr('href'), function (data) {
                        if (data.result.toLowerCase() !== "failure" && data.result.toLowerCase() !== "no subtitles downloaded") {
                            // clear and update the subtitles column with new informations
                            var subtitles = data.subtitles.split(',');
                            subtitlesTd.empty();
                            $.each(subtitles, function (index, language) {
                                if (language !== "" && language !== "und") {
                                    if (index !== subtitles.length - 1) {
                                        subtitlesTd.append($("<i/>").attr({
                                            "class": "sickrage-flags sickrage-flags-" + language
                                        }));
                                    } else {
                                        subtitlesTd.append($("<i/>").attr({
                                            "class": "sickrage-flags sickrage-flags-" + language
                                        }));
                                    }
                                }
                            });
                            // don't allow other searches
                            subtitlesSearchLink.remove();
                        } else {
                            subtitlesSearchLink.remove();
                        }
                    });

                    // don't follow the link
                    return false;
                });
            },

            ajaxEpMergeSubtitles: function () {
                $('.epMergeSubtitles').click(function () {
                    var subtitlesMergeLink = $(this);
                    // fill with the ajax loading gif
                    subtitlesMergeLink.empty();
                    subtitlesMergeLink.append($("<i/>").attr({
                        "class": "fas fa-spinner fa-spin fa-fw",
                        "title": gt("loading")
                    }));
                    $.getJSON($(this).attr('href'), function () {
                        // don't allow other merges
                        subtitlesMergeLink.remove();
                    });
                    // don't follow the link
                    return false;
                });
            }
        },

        browser: {
            defaults: {
                title: gt('Choose Directory'),
                url: '/browser/',
                autocompleteURL: '/browser/complete',
                includeFiles: 0,
                fileTypes: [],
                showBrowseButton: true
            },
            fileBrowserDialog: null,
            currentBrowserPath: null,
            currentRequest: null,

            init: function () {
                SICKRAGE.browser.defaults.url = SICKRAGE.srWebRoot + SICKRAGE.browser.defaults.url;
                SICKRAGE.browser.defaults.autocomplete = SICKRAGE.srWebRoot + SICKRAGE.browser.defaults.autocompleteURL;

                $.fn.fileBrowser = SICKRAGE.browser.fileBrowser;
                $.fn.nFileBrowser = SICKRAGE.browser.nFileBrowser;
            },

            browse: function (path, endpoint, includeFiles, fileTypes) {
                if (SICKRAGE.browser.currentBrowserPath === path) {
                    return;
                }

                SICKRAGE.browser.currentBrowserPath = path;
                if (SICKRAGE.browser.currentRequest) {
                    SICKRAGE.browser.currentRequest.abort();
                }

                //SICKRAGE.browser.fileBrowserDialog.dialog('option', 'dialogClass', 'browserDialog busy');

                SICKRAGE.browser.currentRequest = $.getJSON(endpoint, {
                    path: path,
                    includeFiles: includeFiles,
                    fileTypes: fileTypes.join(',')
                }, function (data) {
                    SICKRAGE.browser.fileBrowserDialog.find('.modal-body').empty();
                    var firstVal = data[0];
                    var i = 0;
                    var list, link = null;
                    data = $.grep(data, function () {
                        return i++ !== 0;
                    });

                    $('<input class="form-control mb-1">')
                        .val(firstVal.currentPath)
                        .on('keypress', function (e) {
                            if (e.which === 13) {
                                SICKRAGE.browser.browse(e.target.value, endpoint, includeFiles, fileTypes);
                            }
                        })
                        .appendTo(SICKRAGE.browser.fileBrowserDialog.find('.modal-body'))
                        .fileBrowser({showBrowseButton: false})
                        .on('autocompleteselect', function (e, ui) {
                            SICKRAGE.browser.browse(ui.item.value, endpoint, includeFiles, fileTypes);
                        });


                    list = $('<div class="list-group">').appendTo(SICKRAGE.browser.fileBrowserDialog.find('.modal-body'));
                    $.each(data, function (i, entry) {
                        if (entry.isFile && fileTypes &&
                            (!entry.isAllowed || fileTypes.indexOf("images") !== -1 && !entry.isImage)) {
                            return true;
                        }
                        link = $('<a href="javascript:void(0)">').on('click', function () {
                            if (entry.isFile) {
                                SICKRAGE.browser.currentBrowserPath = entry.path;
                                SICKRAGE.browser.fileBrowserDialog.find('.modal-footer .btn-success').click();
                            } else {
                                SICKRAGE.browser.browse(entry.path, endpoint, includeFiles, fileTypes);
                            }
                        }).text(entry.name);

                        if (entry.isImage) {
                            link.prepend('<span class="fas fa-file-image ml-1 mr-1"></span>');
                        } else if (entry.isFile) {
                            link.prepend('<span class="fas fa-file ml-1 mr-1"></span>');
                        } else {
                            link.prepend('<span class="fas fa-folder ml-1 mr-1"></span>')
                                .on('mouseenter', function () {
                                    $('span', this).addClass('fa-folder-open');
                                })
                                .on('mouseleave', function () {
                                    $('span', this).removeClass('fa-folder-open');
                                });
                        }
                        link.appendTo(list);
                    });
                    $('a', list).wrap('<div class="list-group-item list-group-item-action list-group-item-dark p-0">');
                    //SICKRAGE.browser.fileBrowserDialog.dialog('option', 'dialogClass', 'browserDialog');
                });
            },

            nFileBrowser: function (callback, options) {
                options = $.extend({}, SICKRAGE.browser.defaults, options);

                // make a fileBrowserDialog object if one doesn't exist already
                if (!SICKRAGE.browser.fileBrowserDialog) {
                    // set up the jquery dialog
                    SICKRAGE.browser.fileBrowserDialog = $('#fileBrowserDialog').modal();
                    SICKRAGE.browser.fileBrowserDialog.find('.modal-body').addClass('ui-front');
                    SICKRAGE.browser.fileBrowserDialog.find('.modal-title').text(options.title);
                    SICKRAGE.browser.fileBrowserDialog.find('.modal-footer .btn-success').click(function () {
                        callback(SICKRAGE.browser.currentBrowserPath, options);
                        SICKRAGE.browser.fileBrowserDialog.modal('hide');
                    });
                } else {
                    // The title may change, even if fileBrowserDialog already exists
                    SICKRAGE.browser.fileBrowserDialog.find('.modal-title').text(options.title);
                }

                // set up the browser and launch the dialog
                var initialDir = '';
                if (options.initialDir) {
                    initialDir = options.initialDir;
                }

                SICKRAGE.browser.browse(initialDir, options.url, options.includeFiles, options.fileTypes);
                SICKRAGE.browser.fileBrowserDialog.modal();

                return false;
            },

            fileBrowser: function (options) {
                options = $.extend({}, SICKRAGE.browser.defaults, options);
                options.field = $(this);

                if (options.field.autocomplete && options.autocompleteURL) {
                    var query = '';
                    options.field.autocomplete({
                        position: {my: "top", at: "bottom", collision: "flipfit"},
                        source: function (request, response) {
                            //keep track of user submitted search term
                            query = $.ui.autocomplete.escapeRegex(request.term, options.includeFiles);
                            $.ajax({
                                url: options.autocompleteURL,
                                data: request,
                                dataType: "json",
                                success: function (data) {
                                    //implement a startsWith filter for the results
                                    var matcher = new RegExp("^" + query, "i");
                                    var a = $.grep(data, function (item) {
                                        return matcher.test(item);
                                    });
                                    response(a);
                                }
                            });
                        },
                        open: function () {
                            $(".ui-autocomplete li.ui-menu-item a").removeClass("ui-corner-all");
                        }
                    }).data("ui-autocomplete")._renderItem = function (ul, item) {
                        //highlight the matched search term from the item -- note that this is global and will match anywhere
                        var result_item = item.label;
                        var x = new RegExp("(?![^&;]+;)(?!<[^<>]*)(" + query + ")(?![^<>]*>)(?![^&;]+;)", "gi");
                        result_item = result_item.replace(x, function (FullMatch) {
                            return '<b>' + FullMatch + '</b>';
                        });
                        return $("<li></li>")
                            .data("ui-autocomplete-item", item)
                            .append("<a class='text-nowrap'>" + result_item + "</a>")
                            .appendTo(ul);
                    };
                }

                var path, callback, ls = false;

                try {
                    ls = !!(localStorage.getItem);
                } catch (e) {
                    ls = null;
                }
                if (ls && options.key) {
                    path = localStorage['fileBrowser-' + options.key];
                }
                if (options.key && options.field.val().length === 0 && (path)) {
                    options.field.val(path);
                }

                callback = function (path, options) {
                    // store the browsed path to the associated text field
                    options.field.val(path);

                    // use a localStorage to remember for next time -- no ie6/7
                    if (ls && options.key) {
                        localStorage['fileBrowser-' + options.key] = path;
                    }

                };

                // append the browse button and give it a click behaviour
                options.field.addClass('fileBrowserField');
                if (options.showBrowseButton) {
                    // append the browse button and give it a click behaviour
                    options.field.after(
                        $('<div class="input-group-append"><span class="input-group-text"><a href="#" class="fileBrowser fas fa-search""></a></span></div>').on('click', function () {
                            var initialDir = options.field.val() || (options.key && path) || '';
                            var optionsWithInitialDir = $.extend({}, options, {initialDir: initialDir});
                            $(this).nFileBrowser(callback, optionsWithInitialDir);
                            return false;
                        })
                    );
                }
                return options.field;
            }
        },

        root_dirs: {
            init: function () {
                var methods = [
                    'assert',
                    'clear',
                    'count',
                    'debug',
                    'dir',
                    'dirxml',
                    'error',
                    'exception',
                    'group',
                    'groupCollapsed',
                    'groupEnd',
                    'info',
                    'log',
                    'markTimeline',
                    'profile',
                    'profileEnd',
                    'table',
                    'time',
                    'timeEnd',
                    'timeStamp',
                    'trace',
                    'warn'
                ];

                var length = methods.length;
                var console = (window.console = window.console || {});

                while (length--) {
                    // Only stub undefined methods.
                    var method = methods[length];
                    if (!console[method]) {
                        console[method] = function () {
                        };
                    }
                }

                $('#addRootDir').click(function () {
                    $(this).nFileBrowser(SICKRAGE.root_dirs.addRootDir);
                });

                $('#editRootDir').click(function () {
                    $(this).nFileBrowser(SICKRAGE.root_dirs.editRootDir, {initialDir: $("#rootDirs option:selected").val()});
                });

                $('#deleteRootDir').click(function () {
                    if ($("#rootDirs option:selected").length) {

                        var toDelete = $("#rootDirs option:selected");

                        var newDefault = (toDelete.attr('id') === $("#whichDefaultRootDir").val());
                        var deletedNum = $("#rootDirs option:selected").attr('id').substr(3);

                        toDelete.remove();
                        SICKRAGE.root_dirs.syncOptionIDs();

                        if (newDefault) {

                            console.log('new default when deleting');

                            // we deleted the default so this isn't valid anymore
                            $("#whichDefaultRootDir").val('');

                            // if we're deleting the default and there are options left then pick a new default
                            if ($("#rootDirs option").length) {
                                SICKRAGE.root_dirs.setDefault($('#rootDirs option').attr('id'));
                            }

                        } else if ($("#whichDefaultRootDir").val().length) {
                            var oldDefaultNum = $("#whichDefaultRootDir").val().substr(3);
                            if (oldDefaultNum > deletedNum) {
                                $("#whichDefaultRootDir").val('rd-' + (oldDefaultNum - 1));
                            }
                        }

                    }

                    SICKRAGE.root_dirs.refreshRootDirs();
                    $.get(SICKRAGE.srWebRoot + '/config/general/saveRootDirs', {rootDirString: $('#rootDirText').val()});
                });

                $('#defaultRootDir').click(function () {
                    if ($("#rootDirs option:selected").length) {
                        SICKRAGE.root_dirs.setDefault($("#rootDirs option:selected").attr('id'));
                    }
                    SICKRAGE.root_dirs.refreshRootDirs();
                    $.get(SICKRAGE.srWebRoot + '/config/general/saveRootDirs', {rootDirString: $('#rootDirText').val()});
                });

                $('#rootDirs').click(function () {
                    SICKRAGE.root_dirs.refreshRootDirs();
                });

                SICKRAGE.root_dirs.syncOptionIDs();
                SICKRAGE.root_dirs.setDefault($('#whichDefaultRootDir').val(), true);
                SICKRAGE.root_dirs.refreshRootDirs();
            },

            addRootDir: function (path) {
                if (!path.length) {
                    return;
                }

                // check if it's the first one
                var isDefault = false;
                if (!$('#whichDefaultRootDir').val().length) {
                    isDefault = true;
                }

                $('#rootDirs').append('<option value="' + path + '">' + path + '</option>');

                SICKRAGE.root_dirs.syncOptionIDs();

                if (isDefault) {
                    SICKRAGE.root_dirs.setDefault($('#rootDirs option').attr('id'));
                }

                SICKRAGE.root_dirs.refreshRootDirs();
                $.get(SICKRAGE.srWebRoot + '/config/general/saveRootDirs', {rootDirString: $('#rootDirText').val()});

                return false;
            },

            editRootDir: function (path) {
                if (!path.length) {
                    return;
                }

                // as long as something is selected
                if ($("#rootDirs option:selected").length) {

                    // update the selected one with the provided path
                    if ($("#rootDirs option:selected").attr('id') === $("#whichDefaultRootDir").val()) {
                        $("#rootDirs option:selected").text('*' + path);
                    } else {
                        $("#rootDirs option:selected").text(path);
                    }
                    $("#rootDirs option:selected").val(path);
                }

                SICKRAGE.root_dirs.refreshRootDirs();
                $.get(SICKRAGE.srWebRoot + '/config/general/saveRootDirs', {rootDirString: $('#rootDirText').val()});
            },

            setDefault: function (which, force) {
                if (which !== undefined && !which.length) {
                    return;
                }

                if ($('#whichDefaultRootDir').val() === which && force !== true) {
                    return;
                }

                // put an asterisk on the text
                if ($('#' + which).text().charAt(0) !== '*') {
                    $('#' + which).text('*' + $('#' + which).text());
                }

                // if there's an existing one then take the asterisk off
                if ($('#whichDefaultRootDir').val() && force !== true) {
                    var oldDefault = $('#' + $('#whichDefaultRootDir').val());
                    oldDefault.text(oldDefault.text().substring(1));
                }

                $('#whichDefaultRootDir').val(which);
            },

            syncOptionIDs: function () {
                // re-sync option ids
                var i = 0;
                $('#rootDirs option').each(function () {
                    $(this).attr('id', 'rd-' + (i++));
                });
            },

            refreshRootDirs: function () {
                if (!$("#rootDirs").length) {
                    return;
                }

                var doDisable = 'true';

                // re-sync option ids
                SICKRAGE.root_dirs.syncOptionIDs();

                // if nothing's selected then select the default
                if (!$("#rootDirs option:selected").length && $('#whichDefaultRootDir').val().length) {
                    $('#' + $('#whichDefaultRootDir').val()).prop("selected", true);
                }

                // if something's selected then we have some behavior to figure out
                if ($("#rootDirs option:selected").length) {
                    doDisable = '';
                }

                // update the elements
                $('#deleteRootDir').prop('disabled', doDisable);
                $('#defaultRootDir').prop('disabled', doDisable);
                $('#editRootDir').prop('disabled', doDisable);

                //var logString = '';
                var dirString = '';

                if ($('#whichDefaultRootDir').val().length >= 4) {
                    dirString = $('#whichDefaultRootDir').val().substr(3);
                }

                $('#rootDirs option').each(function () {
                    //logString += $(this).val() + '=' + $(this).text() + '->' + $(this).attr('id') + '\n';
                    if (dirString.length) {
                        dirString += '|' + $(this).val();
                    }
                });

                //logString += 'def: ' + $('#whichDefaultRootDir').val();

                $('#rootDirText').val(dirString);
                $('#rootDirText').change();
            }
        },

        quality_chooser: {
            init: function () {
                $('#qualityPreset').change(function () {
                    SICKRAGE.quality_chooser.setFromPresets($('#qualityPreset :selected').val());
                });

                SICKRAGE.quality_chooser.setFromPresets($('#qualityPreset :selected').val());
            },

            setFromPresets: function (preset) {
                if (parseInt(preset) === 0) {
                    $('#qualityPreset_label').hide();
                    $('#customQuality').show();
                    return;
                } else {
                    $('#customQuality').hide();
                    $('#qualityPreset_label').show();
                }

                $('#anyQualities option').each(function () {
                    var result = preset & $(this).val();
                    if (result > 0) {
                        $(this).attr('selected', 'selected');
                    } else {
                        $(this).attr('selected', false);
                    }
                });

                $('#bestQualities option').each(function () {
                    var result = preset & ($(this).val() << 16);
                    if (result > 0) {
                        $(this).attr('selected', 'selected');
                    } else {
                        $(this).attr('selected', false);
                    }
                });
            }
        },

        root: {
            init: function () {
            },

            schedule: function () {
                SICKRAGE.ajax_search.init();

                $.backstretch(SICKRAGE.srWebRoot + '/images/backdrops/schedule.jpg');
                $('.backstretch').css("opacity", SICKRAGE.getMeta('sickrage.FANART_BACKGROUND_OPACITY')).fadeIn("500");

                if (SICKRAGE.isMeta('sickrage.COMING_EPS_LAYOUT', ['list'])) {
                    var sortCodes = {'date': 0, 'show': 2, 'network': 5};
                    var sort = SICKRAGE.getMeta('sickrage.COMING_EPS_SORT');
                    var sortList = (sort in sortCodes) ? [[sortCodes[sort], 0]] : [[0, 0]];

                    $('#showListTable:has(tbody tr)').tablesorter({
                        theme: 'bootstrap',
                        widgets: ['stickyHeaders', 'filter', 'columnSelector', 'saveSort'],
                        sortList: sortList,
                        textExtraction: {
                            0: function (node) {
                                return $(node).find('time').attr('datetime');
                            },
                            1: function (node) {
                                return $(node).find('time').attr('datetime');
                            },
                            7: function (node) {
                                return $(node).find('span').text().toLowerCase();
                            }
                        },
                        headers: {
                            0: {sorter: 'realISODate'},
                            1: {sorter: 'realISODate'},
                            2: {sorter: 'loadingNames'},
                            4: {sorter: 'loadingNames'},
                            7: {sorter: 'quality'},
                            8: {sorter: false},
                            9: {sorter: false}
                        },
                        widgetOptions: (function () {
                            if (SICKRAGE.metaToBool('sickrage.FILTER_ROW')) {
                                return {
                                    filter_columnFilters: true,
                                    filter_hideFilters: true,
                                    filter_saveFilters: true,
                                    columnSelector_mediaquery: false
                                };
                            } else {
                                return {
                                    filter_columnFilters: false,
                                    columnSelector_mediaquery: false
                                };
                            }
                        }())
                    });
                }

                if (SICKRAGE.isMeta('sickrage.COMING_EPS_LAYOUT', ['banner', 'poster'])) {
                    $('.ep_summary').hide();
                    $('.ep_summaryTrigger').click(function () {
                        $(this).next('.ep_summary').slideToggle('normal', function () {
                            $.prev('.ep_summaryTrigger').attr('src', function (i, src) {
                                return $(this).next('.ep_summary').is(':visible') ? src.replace('plus', 'minus') : src.replace('minus', 'plus');
                            });
                        });
                    });
                }

                $('#popover').popover({
                    placement: 'bottom',
                    html: true, // required if content has HTML
                    content: '<div id="popover-target"></div>'
                }).on('shown.bs.popover', function () { // bootstrap popover event triggered when the popover opens
                    // call this function to copy the column selection code into the popover
                    $.tablesorter.columnSelector.attachTo($('#showListTable'), '#popover-target');
                });
            },

            history: function () {
                $.backstretch(SICKRAGE.srWebRoot + '/images/backdrops/history.jpg');
                $('.backstretch').css("opacity", SICKRAGE.getMeta('sickrage.FANART_BACKGROUND_OPACITY')).fadeIn("500");

                $("#historyTable:has(tbody tr)").tablesorter({
                    theme: 'bootstrap',
                    widgets: ['filter'],
                    sortList: [[0, 1]],
                    textExtraction: (function () {
                        if (SICKRAGE.isMeta('sickrage.HISTORY_LAYOUT', ['detailed'])) {
                            return {
                                0: function (node) {
                                    return $(node).find('time').attr('datetime');
                                },
                                4: function (node) {
                                    return $(node).find("span").text().toLowerCase();
                                }
                            };
                        } else {
                            return {
                                0: function (node) {
                                    return $(node).find('time').attr('datetime');
                                },
                                1: function (node) {
                                    return $(node).find("span").text().toLowerCase();
                                },
                                2: function (node) {
                                    return $(node).attr("data-provider").toLowerCase();
                                },
                                5: function (node) {
                                    return $(node).attr("data-quality").toLowerCase();
                                }
                            };
                        }
                    }()),
                    headers: (function () {
                        if (SICKRAGE.isMeta('sickrage.HISTORY_LAYOUT', ['detailed'])) {
                            return {
                                0: {sorter: 'realISODate'},
                                4: {sorter: 'data-quality'}
                            };
                        } else {
                            return {
                                0: {sorter: 'realISODate'},
                                4: {sorter: false},
                                5: {sorter: 'data-quality'}
                            };
                        }
                    }())
                });

                $('#history_limit').on('change', function () {
                    window.location.href = SICKRAGE.srWebRoot + '/history/?limit=' + $(this).val();
                });

                $('a.clearhistory').confirm({
                    theme: 'dark',
                    title: gt('Clear History'),
                    content: gt('Are you sure you want to clear all download history ?')
                });

                $('a.trimhistory').confirm({
                    theme: 'dark',
                    title: gt('Trim History'),
                    content: gt('Are you sure you want to trim all download history older than 30 days ?')
                });
            },

            api_builder: function () {
                // Perform an API call
                $('[data-action=api-call]').on('click', function () {
                    var parameters = $('[data-command=' + $(this).data('command-name') + ']');
                    var profile = $('#option-profile').is(':checked');
                    var targetId = $(this).data('target');
                    var timeId = $(this).data('time');
                    var url = $('#' + $(this).data('base-url')).text();
                    var urlId = $(this).data('url');

                    $.each(parameters, function (index, item) {
                        var name = $(item).attr('name');
                        var value = $(item).val();

                        if (name !== undefined && value !== undefined && name !== value && value) {
                            if ($.isArray(value)) {
                                value = value.join('|');
                            }

                            url += '&' + name + '=' + value;
                        }
                    });

                    if (profile) {
                        url += '&profile=1';
                    }

                    var requestTime = new Date().getTime();
                    $.get(url, function (data, textStatus, jqXHR) {
                        var responseTime = new Date().getTime() - requestTime;
                        var jsonp = $('#option-jsonp').is(':checked');
                        var responseType = jqXHR.getResponseHeader('content-type') || '';
                        var target = $(targetId);

                        $(timeId).text(responseTime + 'ms');
                        $(urlId).text(url + (jsonp ? '&jsonp=foo' : ''));

                        if (responseType.slice(0, 6) === 'image/') {
                            target.html($('<img/>').attr('src', url));
                        } else {
                            var json = JSON.stringify(data, null, 4);

                            if (jsonp) {
                                target.text('foo(' + json + ');');
                            } else {
                                target.text(json);
                            }
                        }

                        target.parents('.result-wrapper').removeClass('d-none');
                    });
                });

                // Remove the result of an API call
                $('[data-action=clear-result]').on('click', function () {
                    $($(this).data('target')).html('').parents('.result-wrapper').addClass('d-none');
                });

                // Update the list of episodes
                $('[data-action=update-episodes]').on('change', function () {
                    var command = $(this).data('command');
                    var select = $('[data-command=' + command + '][name=episode]');
                    var season = $(this).val();
                    var show = $('[data-command=' + command + '][name=indexerid]').val();
                    var episodes = $.parseJSON(SICKRAGE.getMeta('episodes'));

                    if (select !== undefined) {
                        select.removeClass('d-none');
                        select.find('option:gt(0)').remove();

                        for (var episode in episodes[show][season]) {
                            if (Object.prototype.hasOwnProperty.call(episodes[show][season], episode)) {
                                select.append($('<option>', {
                                    value: episode,
                                    label: 'Episode ' + episode
                                }));
                            }
                        }
                    }
                });

                // Update the list of seasons
                $('[data-action=update-seasons]').on('change', function () {
                    var command = $(this).data('command');
                    var select = $('[data-command=' + command + '][name=season]');
                    var show = $(this).val();
                    var episodes = $.parseJSON(SICKRAGE.getMeta('episodes'));

                    if (select !== undefined) {
                        select.removeClass('d-none');
                        select.find('option:gt(0)').remove();

                        for (var season in episodes[show]) {
                            if (Object.prototype.hasOwnProperty.call(episodes[show], season)) {
                                select.append($('<option>', {
                                    value: season,
                                    label: (season === 0) ? 'Specials' : 'Season ' + season
                                }));
                            }
                        }
                    }
                });

                // Enable command search
                //$('#command-search').typeahead({
                //    source: SICKRAGE.getMeta('commands')
                //});

                //$('#command-search').on('change', function () {
                //    var command = $(this).typeahead('getActive');

                //if (command) {
                //    var commandId = command.replace('.', '-');
                //    $('[href=#command-' + commandId + ']').click();
                //}
                //});
            },

            announcements: function () {
                $('.mark-seen').on('click', function () {
                    let elm = $(this);
                    $.post(SICKRAGE.srWebRoot + "/announcements/mark-seen", {
                        ahash: $(this).closest('.announcement')[0].id
                    }, function () {
                        SICKRAGE.updateProfileBadge();
                        elm.hide()
                    });
                });
            }
        },

        home: {
            init: function () {
                $.backstretch(SICKRAGE.srWebRoot + '/images/backdrops/home.jpg');
                $('.backstretch').css("opacity", SICKRAGE.getMeta('sickrage.FANART_BACKGROUND_OPACITY')).fadeIn("500");
            },

            index: function () {
                const progressbarObserver = new IntersectionObserver((entries, observer) => {
                    entries.forEach((entry) => {
                        if (entry.isIntersecting) {
                            $.getJSON(SICKRAGE.srWebRoot + '/home/showProgress', {
                                'show-id': $(entry.target).data('show-id')
                            }, function (data) {
                                const percentage = data.progressbar_percent;
                                const classToAdd = percentage === 100 ? 100 : percentage > 80 ? 80 : percentage > 60 ? 60 : percentage > 40 ? 40 : 20;
                                $(entry.target).append('<div class="progressbarText" title="' + data.progress_tip + '">' + data.progress_text + '</div>');
                                $(entry.target).css({width: percentage + '%'});
                                $(entry.target).addClass('progress-' + classToAdd);
                                observer.unobserve(entry.target);
                            });
                        }
                    })
                });

                document.querySelectorAll('div.progress-bar').forEach(item => {
                    progressbarObserver.observe(item)
                });

                function resizePosters(newSize) {
                    var fontSize, spriteScale, borderRadius;
                    if (newSize < 125) { // small
                        borderRadius = 3;
                    } else if (newSize < 175) { // medium
                        fontSize = 9;
                        spriteScale = .6;
                        borderRadius = 4;
                    } else { // large
                        fontSize = 11;
                        spriteScale = 1;
                        borderRadius = 6;
                    }

                    $('#posterPopup').remove();

                    if (fontSize === undefined) {
                        $('.show-details').hide();
                    } else {
                        $('.show-details').show();
                        $('.show-dlstats, .show-quality').css('fontSize', fontSize);
                        $('.show-network-image').css('transform', `scale(${spriteScale})`);
                    }

                    $('.show-container').css({
                        width: newSize,
                        borderRadius: borderRadius
                    });
                }

                $('#posterSizeSlider').slider({
                    min: 75,
                    max: 250,
                    value: localStorage.posterSize || 188,
                    change: function (e, ui) {
                        if (window.localStorage) {
                            localStorage.setItem('posterSize', ui.value);
                        }
                        resizePosters(ui.value);
                        $('.show-grid').isotope('layout');
                    }
                });

                $("#showListTableShows:has(tbody tr), #showListTableAnime:has(tbody tr)").tablesorter({
                    theme: 'bootstrap',
                    sortList: [[7, 1], [2, 0]],
                    textExtraction: {
                        0: function (node) {
                            return $(node).find('time').attr('datetime');
                        },
                        1: function (node) {
                            return $(node).find('time').attr('datetime');
                        },
                        3: function (node) {
                            return $(node).find("span").text().toLowerCase();
                        },
                        4: function (node) {
                            return $(node).find("span").text().toLowerCase();
                        },
                        5: function (node) {
                            return $(node).find("span:first").text();
                        },
                        6: function (node) {
                            return $(node).data('show-size');
                        },
                        7: function (node) {
                            return $(node).find("span").text().toLowerCase();
                        }
                    },
                    widgets: ['saveSort', 'stickyHeaders', 'filter', 'columnSelector'],
                    headers: (function () {
                        if (SICKRAGE.metaToBool('sickrage.FILTER_ROW')) {
                            return {
                                0: {sorter: 'realISODate'},
                                1: {sorter: 'realISODate'},
                                2: {sorter: 'loadingNames'},
                                4: {sorter: 'quality'},
                                5: {sorter: 'eps'},
                                6: {sorter: 'digit'},
                                7: {filter: 'parsed'}
                            };
                        } else {
                            return {
                                0: {sorter: 'realISODate'},
                                1: {sorter: 'realISODate'},
                                2: {sorter: 'loadingNames'},
                                4: {sorter: 'quality'},
                                5: {sorter: 'eps'},
                                6: {sorter: 'digit'}
                            };
                        }
                    }()),
                    widgetOptions: (function () {
                        if (SICKRAGE.metaToBool('sickrage.FILTER_ROW')) {
                            return {
                                filter_columnFilters: true,
                                filter_hideFilters: true,
                                // filter_saveFilters: true,
                                filter_functions: {
                                    5: function (e, n, f) {
                                        var test = false;
                                        var pct = Math.floor((n % 1) * 1000);
                                        if (f === '') {
                                            test = true;
                                        } else {
                                            var result = f.match(/(<|<=|>=|>)\s(\d+)/i);
                                            if (result) {
                                                if (result[1] === "<") {
                                                    if (pct < parseInt(result[2])) {
                                                        test = true;
                                                    }
                                                } else if (result[1] === "<=") {
                                                    if (pct <= parseInt(result[2])) {
                                                        test = true;
                                                    }
                                                } else if (result[1] === ">=") {
                                                    if (pct >= parseInt(result[2])) {
                                                        test = true;
                                                    }
                                                } else if (result[1] === ">") {
                                                    if (pct > parseInt(result[2])) {
                                                        test = true;
                                                    }
                                                }
                                            }

                                            result = f.match(/(\d+)\s(-|to)\s(\d+)/i);
                                            if (result) {
                                                if ((result[2] === "-") || (result[2] === "to")) {
                                                    if ((pct >= parseInt(result[1])) && (pct <= parseInt(result[3]))) {
                                                        test = true;
                                                    }
                                                }
                                            }

                                            result = f.match(/(=)?\s?(\d+)\s?(=)?/i);
                                            if (result) {
                                                if ((result[1] === "=") || (result[3] === "=")) {
                                                    if (parseInt(result[2]) === pct) {
                                                        test = true;
                                                    }
                                                }
                                            }

                                            if (!isNaN(parseFloat(f)) && isFinite(f)) {
                                                if (parseInt(f) === pct) {
                                                    test = true;
                                                }
                                            }
                                        }
                                        return test;
                                    }
                                },
                                columnSelector_mediaquery: false
                            };
                        } else {
                            return {
                                filter_columnFilters: false
                            };
                        }
                    }()),
                    sortStable: true,
                    sortAppend: [[2, 0]]
                });

                $('.show-grid').imagesLoaded(function () {
                    resizePosters(parseInt(localStorage.posterSize || 188));

                    $('.show-grid').removeClass('d-none');

                    $('.show-grid').isotope({
                        itemSelector: '.show-container',
                        sortBy: SICKRAGE.getMeta('sickrage.POSTER_SORTBY'),
                        sortAscending: SICKRAGE.getMeta('sickrage.POSTER_SORTDIR'),
                        layoutMode: 'masonry',
                        masonry: {
                            isFitWidth: true
                        },
                        getSortData: {
                            name: function (itemElem) {
                                var name = $(itemElem).attr('data-name') || '';
                                return (SICKRAGE.metaToBool('sickrage.SORT_ARTICLE') ? name : name.replace(/^((?:The|A|An)\s)/i, '')).toLowerCase();
                            }
                        }
                    });

                    // When posters are small enough to not display the .show-details
                    // table, display a larger poster when hovering.
                    var posterHoverTimer = null;
                    $('.show-container').on('mouseenter', function () {
                        var poster = $(this);
                        if (poster.find('.show-details').css('display') !== 'none') {
                            return;
                        }
                        posterHoverTimer = setTimeout(function () {
                            posterHoverTimer = null;
                            $('#posterPopup').remove();
                            var popup = poster.clone().attr({
                                id: 'posterPopup'
                            });
                            var origLeft = poster.offset().left;
                            var origTop = poster.offset().top;
                            popup.css({
                                position: 'absolute',
                                margin: 0,
                                top: origTop,
                                left: origLeft,
                                zIndex: 9999
                            });

                            popup.find('.show-details').show();
                            popup.on('mouseleave', function () {
                                $(this).remove();
                            });
                            popup.appendTo('body');

                            var height = 438, width = 250;
                            var newTop = (origTop + poster.height() / 2) - (height / 2);
                            var newLeft = (origLeft + poster.width() / 2) - (width / 2);

                            // Make sure the popup isn't outside the viewport
                            var margin = 5;
                            var scrollTop = $(window).scrollTop();
                            var scrollLeft = $(window).scrollLeft();
                            var scrollBottom = scrollTop + $(window).innerHeight();
                            var scrollRight = scrollLeft + $(window).innerWidth();
                            if (newTop < scrollTop + margin) {
                                newTop = scrollTop + margin;
                            }
                            if (newLeft < scrollLeft + margin) {
                                newLeft = scrollLeft + margin;
                            }
                            if (newTop + height + margin > scrollBottom) {
                                newTop = scrollBottom - height - margin;
                            }
                            if (newLeft + width + margin > scrollRight) {
                                newLeft = scrollRight - width - margin;
                            }

                            popup.animate({
                                top: newTop,
                                left: newLeft,
                                width: 250,
                                height: 438
                            });
                        }, 300);
                    }).on('mouseleave', function () {
                        if (posterHoverTimer !== null) {
                            clearTimeout(posterHoverTimer);
                        }
                    });
                });

                $('#postersort').on('change', function () {
                    var sortValue = $(this).val();
                    $('.show-grid').isotope({sortBy: sortValue});
                    $.post($(this).find('option[value=' + $(this).val() + ']').attr('data-sort'));
                });

                $('#postersortdirection').on('change', function () {
                    var sortDirection = $(this).val() === 'true';
                    $('.show-grid').isotope({sortAscending: sortDirection});
                    $.post($(this).find('option[value=' + $(this).val() + ']').attr('data-sort'));
                });

                $('#popover').popover({
                    placement: 'bottom',
                    html: true, // required if content has HTML
                    content: '<div id="popover-target"></div>'
                }).on('shown.bs.popover', function () { // bootstrap popover event triggered when the popover opens
                    // call this function to copy the column selection code into the popover
                    $.tablesorter.columnSelector.attachTo($('#showListTableShows'), '#popover-target');
                    if ($('#showListTableAnime').length && SICKRAGE.metaToBool('sickrage.ANIME_SPLIT_HOME')) {
                        $.tablesorter.columnSelector.attachTo($('#showListTableAnime'), '#popover-target');
                    }
                });
            },

            display_show: {
                init: function () {
                    SICKRAGE.home.display_show.imdbRating();

                    if (SICKRAGE.metaToBool('sickrage.FANART_BACKGROUND')) {
                        $.backstretch(SICKRAGE.srWebRoot + '/images/' + $('#showID').attr('value') + '.fanart.jpg');
                        $('.backstretch').css("opacity", SICKRAGE.getMeta('sickrage.FANART_BACKGROUND_OPACITY')).fadeIn("500");
                    }

                    $("#showTable, #animeTable").tablesorter({
                        theme: 'bootstrap',
                        widgets: ['saveSort', 'columnSelector'],
                        widgetOptions: {
                            columnSelector_saveColumns: true,
                            columnSelector_layout: '<br><label><input type="checkbox">{name}</label>',
                            columnSelector_mediaquery: false,
                            columnSelector_cssChecked: 'checked'
                        }
                    });

                    $('#popover').popover({
                        placement: 'bottom',
                        html: true, // required if content has HTML
                        content: '<div id="popover-target"></div>'
                    }).on('shown.bs.popover', function () {
                        $('.displayShowTable').each(function (index, item) {
                            $.tablesorter.columnSelector.attachTo(item, '#popover-target');
                        });
                    });

                    $('#seasonJump').on('change', function () {
                        var id = $('#seasonJump option:selected').val();
                        if (id && id !== 'jump') {
                            var season = $('#seasonJump option:selected').data('season');
                            $('html,body').animate({scrollTop: $('[name ="' + id.substring(1) + '"]').offset().top - 50}, 'slow');
                            $('#collapseSeason-' + season).collapse('show');
                            location.hash = id;
                        }
                        $(this).val('jump');
                    });

                    $("#prevShow").on('click', function () {
                        $('#pickShow option:selected').prev().prop('selected', 'selected');
                        $("#pickShow").change();
                    });

                    $("#nextShow").on('click', function () {
                        $('#pickShow option:selected').next().prop('selected', 'selected');
                        $("#pickShow").change();
                    });

                    $('#changeStatus').on('click', function () {
                        var epArr = [];

                        $('.epCheck').each(function () {
                            if ($(this).prop('checked')) {
                                epArr.push($(this).attr('id'));
                            }
                        });

                        if (epArr.length === 0) {
                            return false;
                        }

                        window.location.href = SICKRAGE.srWebRoot + '/manage/setEpisodeStatus?show=' + $('#showID').attr('value') + '&eps=' + epArr.join('|') + '&status=' + $('#statusSelect').val();
                    });

                    $('#deleteEpisode').on('click', function () {
                        var epArr = [];

                        $('.epCheck').each(function () {
                            if ($(this).prop('checked')) {
                                epArr.push($(this).attr('id'));
                            }
                        });

                        if (epArr.length === 0) {
                            return false;
                        }

                        window.location.href = SICKRAGE.srWebRoot + '/home/deleteEpisode?show=' + $('#showID').attr('value') + '&eps=' + epArr.join('|');
                    });

                    $('.seasonCheck').on('click', function () {
                        var seasCheck = this;
                        var seasNo = $(this).attr('id');

                        $('#collapseSeason-' + seasNo).collapse('show');
                        $('.epCheck:visible').each(function () {
                            var epParts = $(this).attr('id').split('x');
                            if (epParts[0] === seasNo) {
                                $(this).prop("checked", seasCheck.checked);
                            }
                        });
                    });

                    var lastCheck = null;
                    $('.epCheck').on('click', function (event) {

                        if (!lastCheck || !event.shiftKey) {
                            lastCheck = this;
                            return;
                        }

                        var check = this;
                        var found = 0;

                        $('.epCheck').each(function () {
                            switch (found) {
                                case 2:
                                    return false;
                                case 1:
                                    $(this).prop("checked", lastCheck.checked);
                            }

                            if ($(this) === check || $(this) === lastCheck) {
                                found++;
                            }
                        });
                    });

                    // selects all visible episode checkboxes.
                    $('.seriesCheck').on('click', function () {
                        $('.epCheck:visible').each(function () {
                            $(this).prop("checked", true);
                        });
                        $('.seasonCheck:visible').each(function () {
                            $(this).prop("checked", true);
                        });
                    });

                    // clears all visible episode checkboxes and the season selectors
                    $('.clearAll').on('click', function () {
                        $('.epCheck:visible').each(function () {
                            $(this).prop("checked", false);
                        });
                        $('.seasonCheck:visible').each(function () {
                            $(this).prop("checked", false);
                        });
                    });

                    // handle the show selection dropbox
                    $('#pickShow').on('change', function () {
                        var val = $(this).val();
                        if (val === 0) {
                            return;
                        }
                        window.location.href = SICKRAGE.srWebRoot + '/home/displayShow?show=' + val;
                    });

                    // show/hide different types of rows when the checkboxes are changed
                    $("#checkboxControls input").change(function () {
                        var whichClass = $(this).attr('id');
                        var status = $('#checkboxControls > input, #' + whichClass).prop('checked');
                        SICKRAGE.showHideRows(whichClass, status);
                    });

                    // initially show/hide all the rows according to the checkboxes
                    $("#checkboxControls input").each(function () {
                        var status = $(this).prop('checked');
                        $("tr." + $(this).attr('id')).each(function () {
                            if (status) {
                                $(this).show();
                            } else {
                                $(this).hide();
                            }
                        });
                    });

                    // hide season headers with no episodes under them
                    $('tr.seasonheader').each(function () {
                        var numRows = 0;
                        var seasonNo = $(this).attr('id');
                        $('tr.' + seasonNo + ' :visible').each(function () {
                            numRows++;
                        });
                        if (numRows === 0) {
                            $(this).hide();
                            $('#' + seasonNo + '-cols').hide();
                        } else {
                            $(this).show();
                            $('#' + seasonNo + '-cols').show();
                        }
                    });


                    $('.sceneSeasonXEpisode').on('change', function () {
                        //	Strip non-numeric characters
                        $(this).val($(this).val().replace(/[^0-9xX]*/g, ''));
                        var forSeason = $(this).attr('data-for-season');
                        var forEpisode = $(this).attr('data-for-episode');
                        var m = $(this).val().match(/^(\d+)x(\d+)$/i);
                        var sceneSeason = null, sceneEpisode = null;
                        if (m) {
                            sceneSeason = m[1];
                            sceneEpisode = m[2];
                        }
                        SICKRAGE.home.display_show.setEpisodeSceneNumbering(forSeason, forEpisode, sceneSeason, sceneEpisode);
                    });

                    $('.sceneAbsolute').on('change', function () {
                        //	Strip non-numeric characters
                        $(this).val($(this).val().replace(/[^0-9xX]*/g, ''));
                        var forAbsolute = $(this).attr('data-for-absolute');

                        var m = $(this).val().match(/^(\d{1,3})$/i);
                        var sceneAbsolute = null;
                        if (m) {
                            sceneAbsolute = m[1];
                        }
                        SICKRAGE.home.display_show.setAbsoluteSceneNumbering(forAbsolute, sceneAbsolute);
                    });

                    SICKRAGE.ajax_search.init();

                    $("a.removeshow").confirm({
                        theme: 'dark',
                        title: gt("Remove Show"),
                        content: gt('Are you sure you want to remove') + '<span class="footerhighlight">' + $('#showtitle').data('showname') + '</span>' + gt(' from the database?') + '<br><br><input type="checkbox" id="deleteFiles" name="deleteFiles"/>&nbsp;<label for="deleteFiles" class="text-danger">' + gt('Check to delete files as well. IRREVERSIBLE') + '</label>',
                        buttons: {
                            confirm: function () {
                                var $deleteFiles = this.$content.find('#deleteFiles').prop('checked');
                                location.href = this.$target.attr('href') + ($deleteFiles ? '&full=1' : '');
                            },
                            cancel: {
                                action: function () {
                                }
                            }
                        }
                    });
                },

                imdbRating: function () {
                    let imdbstars = $('#imdbstars');
                    const rating = imdbstars.data('imdb-rating');
                    const rating_star = $('<i>').addClass('fas fa-star text-warning');
                    for (var i = 0; i < rating; i++) {
                        imdbstars.append(rating_star.clone());
                    }
                },

                setEpisodeSceneNumbering: function (forSeason, forEpisode, sceneSeason, sceneEpisode) {
                    var showId = $('#showID').val();
                    var indexer = $('#indexer').val();

                    if (sceneSeason === '') {
                        sceneSeason = null;
                    }
                    if (sceneEpisode === '') {
                        sceneEpisode = null;
                    }

                    $.getJSON(SICKRAGE.srWebRoot + '/home/setSceneNumbering', {
                        'show': showId,
                        'indexer': indexer,
                        'forSeason': forSeason,
                        'forEpisode': forEpisode,
                        'sceneSeason': sceneSeason,
                        'sceneEpisode': sceneEpisode
                    }, function (data) {
                        //	Set the values we get back
                        if (data.sceneSeason === null || data.sceneEpisode === null) {
                            $('#sceneSeasonXEpisode_' + showId + '_' + forSeason + '_' + forEpisode).val('');
                        } else {
                            $('#sceneSeasonXEpisode_' + showId + '_' + forSeason + '_' + forEpisode).val(data.sceneSeason + 'x' + data.sceneEpisode);
                        }
                        if (!data.success) {
                            if (data.errorMessage) {
                                alert(data.errorMessage);
                            } else {
                                alert(gt('Update failed.'));
                            }
                        }
                    });
                },

                setAbsoluteSceneNumbering: function (forAbsolute, sceneAbsolute) {
                    var showId = $('#showID').val();
                    var indexer = $('#indexer').val();

                    if (sceneAbsolute === '') {
                        sceneAbsolute = null;
                    }

                    $.getJSON(SICKRAGE.srWebRoot + '/home/setSceneNumbering', {
                            'show': showId,
                            'indexer': indexer,
                            'forAbsolute': forAbsolute,
                            'sceneAbsolute': sceneAbsolute
                        },
                        function (data) {
                            //	Set the values we get back
                            if (data.sceneAbsolute === null) {
                                $('#sceneAbsolute_' + showId + '_' + forAbsolute).val('');
                            } else {
                                $('#sceneAbsolute_' + showId + '_' + forAbsolute).val(data.sceneAbsolute);
                            }
                            if (!data.success) {
                                if (data.errorMessage) {
                                    alert(data.errorMessage);
                                } else {
                                    alert(gt('Update failed.'));
                                }
                            }
                        });
                }
            },

            edit_show: {
                init: function () {
                    var allExceptions = [];

                    $('#location').fileBrowser({title: gt('Select Show Location')});

                    $('#submit').click(function () {
                        var allExceptions = [];

                        $("#exceptions_list option").each(function () {
                            allExceptions.push($(this).val());
                        });

                        $("#exceptions_list").val(allExceptions);

                        if (SICKRAGE.metaToBool('show.is_anime')) {
                            SICKRAGE.home.generate_bwlist();
                        }
                    });

                    $('#addSceneName').click(function () {
                        var sceneEx = $('#SceneName').val();
                        var option = $("<option>");
                        allExceptions = [];

                        $("#exceptions_list option").each(function () {
                            allExceptions.push($(this).val());
                        });

                        $('#SceneName').val('');

                        if ($.inArray(sceneEx, allExceptions) > -1 || (sceneEx === '')) {
                            return;
                        }

                        $("#SceneException").show();

                        option.attr("value", sceneEx);
                        option.html(sceneEx);
                        return option.appendTo('#exceptions_list');
                    });

                    $('#removeSceneName').click(function () {
                        $('#exceptions_list option:selected').remove();

                        SICKRAGE.home.edit_show.toggleSceneException();
                    });

                    SICKRAGE.home.edit_show.toggleSceneException();
                },

                toggleSceneException: function () {
                    var allExceptions = [];

                    $("#exceptions_list option").each(function () {
                        allExceptions.push($(this).val());
                    });

                    if (allExceptions === '') {
                        $("#SceneException").hide();
                    } else {
                        $("#SceneException").show();
                    }
                }
            },

            add_shows: function () {
                $.backstretch(SICKRAGE.srWebRoot + '/images/backdrops/addshows.jpg');
                $('.backstretch').css("opacity", SICKRAGE.getMeta('sickrage.FANART_BACKGROUND_OPACITY')).fadeIn("500");
            },

            add_existing_shows: {
                init: function () {
                    SICKRAGE.home.add_show_options();
                    SICKRAGE.root_dirs.init();

                    $('#tableDiv').on('click', '#checkAll', function () {
                        $('.dirCheck').not(this).prop('checked', this.checked);
                    });

                    $('#submitShowDirs').on('click', function () {
                        var selectedShows = false;
                        var submitForm = $('#addShowForm');

                        $('.dirCheck').each(function () {
                            if (this.checked === true) {
                                var show = $(this).attr('id');
                                var indexer = $(this).closest('tr').find('select').val();
                                $('<input>', {
                                    type: 'hidden',
                                    name: 'shows_to_add',
                                    value: indexer + '|' + show
                                }).appendTo(submitForm);
                                selectedShows = true;
                            }
                        });

                        if (selectedShows === false) {
                            return false;
                        }

                        $('<input>', {
                            type: 'hidden',
                            name: 'promptForSettings',
                            value: $('#promptForSettings').prop('checked') ? 'on' : 'off'
                        }).appendTo(submitForm);

                        submitForm.submit();
                    });

                    var lastTxt = '';
                    $('#rootDirText').on('change', function () {
                        if (lastTxt === $('#rootDirText').val()) {
                            return false;
                        } else {
                            lastTxt = $('#rootDirText').val();
                        }
                        $('#rootDirStaticList').html('');
                        $('#rootDirs option').each(function (i, w) {
                            $('#rootDirStaticList').append('<div class="list-group-item-dark mb-1"><div class="align-middle m-1"><label class="form-check-label" for="\' + $(w).val() + \'"><input type="checkbox" class="dir_check" id="' + $(w).val() + '" checked=checked><b>' + $(w).val() + '</b></label></div></div>');
                        });
                        SICKRAGE.home.add_existing_shows.loadContent();
                    });

                    $('#rootDirStaticList').on('click', '.dir_check', SICKRAGE.home.add_existing_shows.loadContent);

                    $('#tableDiv').on('click', '.showManage', function (event) {
                        event.preventDefault();
                        $('html,body').animate({scrollTop: 0}, 1000);
                    });

                    $('#rootDirs option').attr('selected', 'selected').parent().focus();
                    $('#rootDirs option').click();
                },

                loadContent: function () {
                    var url = '';
                    $('.dir_check').each(function (i, w) {
                        if ($(w).is(':checked')) {
                            if (url.length) {
                                url += '&';
                            }
                            url += 'rootDir=' + encodeURIComponent($(w).attr('id'));
                        }
                    });

                    $('#tableDiv').html('<span>' + SICKRAGE.loadingHTML + gt('loading folders...') + '</span>');
                    $.get(SICKRAGE.srWebRoot + '/home/addShows/massAddTable/', url, function (data) {
                        $('#tableDiv').html(data);
                        $("#addRootDirTable").tablesorter({
                            theme: 'bootstrap',
                            sortList: [[1, 0]],
                            headers: {
                                0: {sorter: false}
                            }
                        });
                    });
                }
            },

            postprocess: function () {
                $('#episodeDir').fileBrowser({
                    title: gt('Select Unprocessed Episode Folder'),
                    key: 'postprocessPath'
                });
            },

            trakt_shows: {
                init: function () {
                    // initialise combos for dirty page refreshes
                    $('#showsort').val('original');
                    $('#showsortdirection').val('asc');

                    function resizePosters(newSize) {
                        var fontSize, borderRadius;
                        if (newSize < 125) { // small
                            borderRadius = 3;
                        } else if (newSize < 175) { // medium
                            fontSize = 9;
                            borderRadius = 4;
                        } else { // large
                            fontSize = 11;
                            borderRadius = 6;
                        }

                        $('#posterPopup').remove();

                        if (fontSize === undefined) {
                            $('.show-details').hide();
                        } else {
                            $('.show-details').show();
                        }

                        $('.show-container').css({
                            width: newSize,
                            borderRadius: borderRadius
                        });
                    }

                    $('#posterSizeSlider').slider({
                        min: 75,
                        max: 250,
                        value: localStorage.traktPosterSize || 188,
                        change: function (e, ui) {
                            if (window.localStorage) {
                                localStorage.setItem('traktPosterSize', ui.value);
                            }
                            resizePosters(ui.value);
                            $('.show-grid').isotope('layout');
                        }
                    });

                    resizePosters(parseInt(localStorage.traktPosterSize || 188));

                    $('.show-grid').imagesLoaded(function () {
                        $('.show-grid').isotope({
                            itemSelector: '.show-container',
                            sortBy: 'original-order',
                            layoutMode: 'masonry',
                            masonry: {
                                isFitWidth: true
                            },
                            getSortData: {
                                name: function (itemElem) {
                                    var name = $(itemElem).attr('data-name') || '';
                                    return (SICKRAGE.metaToBool('sickrage.SORT_ARTICLE') ? name : name.replace(/^(The|A|An)\s/i, '')).toLowerCase();
                                },
                                rating: '[data-rating] parseInt',
                                votes: '[data-votes] parseInt'
                            }
                        });
                    });

                    $('#showsort').on('change', function () {
                        var sortCriteria;
                        switch ($(this).value) {
                            case 'original':
                                sortCriteria = 'original-order';
                                break;
                            case 'rating':
                                /* randomise, else the rating_votes can already
                                 * have sorted leaving this with nothing to do.
                                 */
                                $('.show-grid').isotope({sortBy: 'random'});
                                sortCriteria = 'rating';
                                break;
                            case 'rating_votes':
                                sortCriteria = ['rating', 'votes'];
                                break;
                            case 'votes':
                                sortCriteria = 'votes';
                                break;
                            default:
                                sortCriteria = 'name';
                                break;
                        }
                        $('.show-grid').isotope({sortBy: sortCriteria});
                    });

                    $('#showsortdirection').on('change', function () {
                        $('.show-grid').isotope({sortAscending: ('asc' === $(this).value)});
                    });

                    $('#traktlist').on('change', function (e) {
                        document.location.href = SICKRAGE.updateUrlParameter(document.location.href, 'list', e.target.value);
                    });

                    $('#limit').on('change', function (e) {
                        document.location.href = SICKRAGE.updateUrlParameter(document.location.href, 'limit', e.target.value);
                    });
                }
            },

            popular_shows: function () {
                function resizePosters(newSize) {
                    var fontSize, borderRadius;
                    if (newSize < 125) { // small
                        borderRadius = 3;
                    } else if (newSize < 175) { // medium
                        fontSize = 9;
                        borderRadius = 4;
                    } else { // large
                        fontSize = 11;
                        borderRadius = 6;
                    }

                    $('#posterPopup').remove();

                    if (fontSize === undefined) {
                        $('.show-details').hide();
                    } else {
                        $('.show-details').show();
                    }

                    $('.show-container').css({
                        width: newSize,
                        borderRadius: borderRadius
                    });
                }

                $('#posterSizeSlider').slider({
                    min: 75,
                    max: 250,
                    value: localStorage.imdbPosterSize || 188,
                    change: function (e, ui) {
                        if (window.localStorage) {
                            localStorage.setItem('imdbPosterSize', ui.value);
                        }
                        resizePosters(ui.value);
                        $('.show-grid').isotope('layout');
                    }
                });

                resizePosters(parseInt(localStorage.traktPosterSize || 188));

                $('.show-grid').imagesLoaded(function () {
                    $('.show-grid').isotope({
                        itemSelector: '.show-container',
                        sortBy: 'original-order',
                        layoutMode: 'masonry',
                        masonry: {
                            isFitWidth: true
                        },
                        getSortData: {
                            name: function (itemElem) {
                                var name = $(itemElem).attr('data-name') || '';
                                return (SICKRAGE.metaToBool('sickrage.SORT_ARTICLE') ? name : name.replace(/^(The|A|An)\s/i, '')).toLowerCase();
                            },
                            rating: '[data-rating] parseInt',
                            votes: '[data-votes] parseInt'
                        }
                    });
                });

                $('#showsort').on('change', function () {
                    var sortCriteria;
                    switch ($(this).value) {
                        case 'original':
                            sortCriteria = 'original-order';
                            break;
                        case 'rating':
                            /* randomise, else the rating_votes can already
                             * have sorted leaving this with nothing to do.
                             */
                            $('.show-grid').isotope({sortBy: 'random'});
                            sortCriteria = 'rating';
                            break;
                        case 'rating_votes':
                            sortCriteria = ['rating', 'votes'];
                            break;
                        case 'votes':
                            sortCriteria = 'votes';
                            break;
                        default:
                            sortCriteria = 'name';
                            break;
                    }
                    $('.show-grid').isotope({sortBy: sortCriteria});
                });

                $('#showsortdirection').on('change', function () {
                    $('.show-grid').isotope({sortAscending: ('asc' === $(this).value)});
                });
            },

            test_renaming: function () {
                $('.seriesCheck').on('click', function () {
                    var serCheck = this;

                    $('.seasonCheck:visible').each(function () {
                        $(this).prop("checked", serCheck.checked);
                    });

                    $('.epCheck:visible').each(function () {
                        $(this).prop("checked", serCheck.checked);
                    });
                });

                $('.seasonCheck').click(function () {
                    var seasCheck = this;
                    var seasNo = $(seasCheck).attr('id');

                    $('.epCheck:visible').each(function () {
                        var epParts = $(this).attr('id').split('x');

                        if (epParts[0] === seasNo) {
                            $(this).prop("checked", seasCheck.checked);
                        }
                    });
                });

                $('input[type=submit]').on('click', function () {
                    var epArr = [];

                    $('.epCheck').each(function () {
                        if ($(this).prop('checked')) {
                            epArr.push($(this).attr('id'));
                        }
                    });

                    if (epArr.length === 0) {
                        return false;
                    }

                    window.location.href = SICKRAGE.srWebRoot + '/home/doRename?show=' + $('#showID').attr('value') + '&eps=' + epArr.join('|');
                });

            },

            new_show: {
                init: function () {
                    const navListItems = $('div.setup-panel div a'),
                        allWells = $('.setup-content'),
                        allNextBtn = $('.nextBtn');

                    // add new show form validation
                    const form = document.getElementById('addShowForm');
                    if (form) {
                        form.addEventListener('submit', function (event) {
                            if (form.checkValidity() === false) {
                                event.preventDefault();
                                event.stopPropagation();
                            }
                            form.classList.add('was-validated');
                        }, false);
                    }

                    allWells.hide();

                    SICKRAGE.root_dirs.init();
                    SICKRAGE.home.add_show_options();
                    SICKRAGE.quality_chooser.init();

                    if ($('input:hidden[name=whichSeries]').length) {
                        $('#addShowForm')[0].classList.add('was-validated');

                        SICKRAGE.home.update_bwlist($('#providedName').val());

                        navListItems.addClass('disabled');
                        navListItems.removeClass('btn-success').addClass('btn-dark');

                        if ($('#fullShowPath').length) {
                            $('div.setup-panel div a[href="#step-3"]').removeClass('btn-dark').addClass('btn-success');
                            allWells.hide();
                            $('#step-3').show();
                        } else {
                            $('div.setup-panel div a[href="#step-2"]').removeClass('btn-dark').addClass('btn-success');
                            allWells.hide();
                            $('#step-2').show();
                        }
                    }

                    $('#nameToSearch').focus();

                    $('#searchName').click(function () {
                        if ($('#addShowForm')[0].checkValidity() === true) {
                            $('#addShowForm')[0].classList.add('was-validated');
                            $(".nextBtn").removeClass('disabled');
                        }
                    });

                    $('#addShowForm').submit(function () {
                        SICKRAGE.home.generate_bwlist();
                    })

                    navListItems.click(function (e) {
                        e.preventDefault();
                        var $target = $($(this).attr('href')),
                            $item = $(this);

                        if (!$item.hasClass('disabled')) {
                            navListItems.removeClass('btn-success').addClass('btn-dark');
                            $item.removeClass('btn-dark').addClass('btn-success');
                            allWells.hide();
                            $target.show();
                            $target.find('input:eq(0)').focus();
                        }
                    });

                    allNextBtn.click(function () {
                        var curStep = $(this).closest(".setup-content"),
                            curStepID = curStep.attr("id"),
                            nextStepWizard = $('div.setup-panel div a[href="#' + curStepID + '"]').parent().next().children("a"),
                            isValid = true,
                            showName = '';

                        if (curStepID == 'step-1') {
                            // if they've picked a radio button then use that
                            if ($('input:radio[name=whichSeries]:checked').length) {
                                showName = $('input:radio[name=whichSeries]:checked').val().split('|')[4];
                            }
                            // if we provided a show in the hidden field, use that
                            else if ($('input:hidden[name=whichSeries]').length && $('input:hidden[name=whichSeries]').val().length) {
                                showName = $('#providedName').val();
                            }

                            if (showName.length) {
                                SICKRAGE.home.update_bwlist(showName);
                            } else {
                                isValid = false;
                            }
                        }

                        if (curStepID == 'step-2') {
                            if (!$('#rootDirs option').length && !$('#fullShowPath').length) {
                                $('#step-2-messages').empty().html('<div style="color: red;"><b>' + gt('You must add a root TV show directory!') + '</b></div>');
                                isValid = false;
                            }
                        }

                        if (isValid) nextStepWizard.removeClass('disabled').trigger('click');
                    });

                    $('#searchName').on('click', function () {
                        $('#searchName').prop('disabled', true);
                        SICKRAGE.home.new_show.searchIndexers();
                        $('#searchName').prop('disabled', false);
                    });

                    $('#skipShowButton').on('click', function () {
                        $('#skipShow').val('1');
                        $('#addShowForm').submit();
                    });

                    $('#nameToSearch').keypress(function (e) {
                        var keycode = (e.keyCode ? e.keyCode : e.which);
                        if (keycode === 13) {
                            e.preventDefault();
                            $('#searchName').click();
                        }
                    });

                    $('div.setup-panel div a.btn-success').trigger('click');
                },

                searchIndexers: function () {
                    if (!$('#nameToSearch').val().length) {
                        return;
                    }

                    var searchingFor = '<b>' + $('#nameToSearch').val().trim() + '</b> on ' + $('#providedIndexer option:selected').text() + '<br/>';
                    $('#step-1-messages').empty().html('<i id="searchingAnim" class="fas fa-spinner fa-spin fa-fw"></i> searching for ' + searchingFor);

                    $.ajax({
                        url: SICKRAGE.srWebRoot + '/home/addShows/searchIndexersForShowName',
                        data: {
                            'search_term': $('#nameToSearch').val().trim(),
                            'lang': $('#indexerLang').val(),
                            'indexer': $('#providedIndexer').val()
                        },
                        timeout: parseInt($('#indexer_timeout').val(), 10) * 1000,
                        dataType: 'json',
                        error: function () {
                            $('#step-1-messages').empty().html(gt('search timed out, try increasing timeout for indexer'));
                        },
                        success: function (data) {
                            var firstResult = true;
                            var resultStr = '<legend class="legend">' + gt('Search Results:') + '</legend>\n';
                            var checked = '';

                            if (data.results.length === 0) {
                                resultStr += '<b>' + gt('No results found, try a different search or language.') + '</b>';
                            } else {
                                $.each(data.results, function (index, obj) {
                                    if (firstResult && obj[6] !== 'disabled') {
                                        checked = ' checked';
                                        firstResult = false;
                                    } else {
                                        checked = '';
                                    }

                                    var whichSeries = obj.join('|');

                                    resultStr += '<input type="radio" class="pull-left" id="whichSeries" name="whichSeries" value="' + whichSeries.replace(/"/g, "") + '"' + checked + ' ' + obj[6] + ' /> ';
                                    resultStr += '<a href="' + SICKRAGE.anonURL + obj[2] + obj[3] + '&lid=' + data.langid + '" onclick="window.open(this.href, \'_blank\'); return false;" ><b>' + obj[4] + '</b></a>';

                                    if (obj[5] !== null) {
                                        var startDate = new Date(obj[5]);
                                        var today = new Date();
                                        if (startDate > today) {
                                            resultStr += gt(' (will debut on ') + obj[5] + ')';
                                        } else {
                                            resultStr += gt(' (started on ') + obj[5] + ')';
                                        }
                                    }

                                    if (obj[0] !== null) {
                                        resultStr += ' [' + obj[0] + ']';
                                    }

                                    if (obj[6] === 'disabled') {
                                        resultStr += '<div class="d-inline text-danger font-weight-bold">' + gt(' already exists in show library') + '</div>';
                                    }

                                    resultStr += '<br/>';
                                });
                                resultStr += '</ul>';
                            }
                            resultStr += '<br/>';

                            $('#step-1-messages').html(resultStr);
                        }
                    });
                }
            },

            add_show_options: function () {
                $('#saveDefaultsButton').on('click', function () {
                    var anyQualArray = [];
                    var bestQualArray = [];
                    $('#anyQualities option:selected').each(function (i, d) {
                        anyQualArray.push($(d).val());
                    });
                    $('#bestQualities option:selected').each(function (i, d) {
                        bestQualArray.push($(d).val());
                    });

                    $.get(SICKRAGE.srWebRoot + '/config/general/saveAddShowDefaults', {
                        defaultStatus: $('#statusSelect').val(),
                        anyQualities: anyQualArray.join(','),
                        bestQualities: bestQualArray.join(','),
                        defaultFlattenFolders: $('#flatten_folders').prop('checked'),
                        subtitles: $('#subtitles').prop('checked'),
                        anime: $('#anime').prop('checked'),
                        search_format: $('#search_format').val(),
                        defaultStatusAfter: $('#statusSelectAfter').val(),
                        skip_downloaded: $('#skip_downloaded').prop('checked'),
                        add_show_year: $('#add_show_year').prop('checked')
                    });

                    $(this).attr('disabled', true);

                    SICKRAGE.notify('info', gt('Saved Defaults'), gt('Your "add show" defaults have been set to your current selections.'));
                });

                $('#statusSelect, #qualityPreset, #flatten_folders, #anyQualities, #bestQualities, #subtitles, #search_format, #anime, #statusSelectAfter, #skip_downloaded, #add_show_year').change(function () {
                    $('#saveDefaultsButton').attr('disabled', false);
                });
            },

            generate_bwlist: function () {
                var realvalues = [];

                $('#white option').each(function (i, selected) {
                    realvalues[i] = $(selected).val();
                });
                $("#whitelist").val(realvalues.join(","));

                realvalues = [];
                $('#black option').each(function (i, selected) {
                    realvalues[i] = $(selected).val();
                });
                $("#blacklist").val(realvalues.join(","));
            },

            update_bwlist: function (show_name) {
                $('#white').children().remove();
                $('#black').children().remove();
                $('#pool').children().remove();

                if ($('#anime').prop('checked')) {
                    $('#blackwhitelist').show();
                    if (show_name) {
                        $.getJSON(SICKRAGE.srWebRoot + '/home/fetch_releasegroups', {'show_name': show_name}, function (data) {
                            if (data.result === 'success') {
                                $.each(data.groups, function (i, group) {
                                    var option = $("<option>");
                                    option.attr("value", group.name);
                                    option.html(group.name + ' | ' + group.rating + ' | ' + group.range);
                                    option.appendTo('#pool');
                                });
                            }
                        });
                    }
                } else {
                    $('#blackwhitelist').hide();
                }
            },

            server_status: {
                init: function () {
                    $("#schedulerStatusTable").tablesorter({
                        theme: 'bootstrap',
                        widgets: ['saveSort']
                    });

                    $("#queueStatusTable").tablesorter({
                        theme: 'bootstrap',
                        sortList: [[3, 0], [4, 0], [2, 1]],
                        widgets: ['saveSort']
                    });

                    $('.forceSchedulerJob').click(function (e) {
                        e.preventDefault();
                        $.get($(this).data('target'));
                    });
                }
            }
        },

        config: {
            init: function () {
                $.backstretch(SICKRAGE.srWebRoot + '/images/backdrops/config.jpg');
                $('.backstretch').css("opacity", SICKRAGE.getMeta('sickrage.FANART_BACKGROUND_OPACITY')).fadeIn("500");

                // Config form validation
                const form = document.getElementById('configForm');
                if (form) {
                    form.addEventListener('submit', function (event) {
                        if (form.checkValidity() === false) {
                            event.preventDefault();
                            event.stopPropagation();
                        }
                        form.classList.add('was-validated');
                    }, false);
                }

                $('#configForm').ajaxForm({
                    beforeSubmit: function () {
                        // if (SICKRAGE.forms_validation === false) {
                        //     return false
                        // }

                        $('.config_submitter .config_submitter_refresh').each(function () {
                            $(this).attr("disabled", "disabled");
                            $(this).after('<span>' + SICKRAGE.loadingHTML + gt(' Saving...') + '</span>');
                            $(this).hide();
                        });
                    },
                    success: function () {
                        setTimeout(function () {
                            "use strict";
                            $('.config_submitter').each(function () {
                                $(this).removeAttr("disabled");
                                $(this).next().remove();
                                $(this).show();
                            });

                            $('.config_submitter_refresh').each(function () {
                                $(this).removeAttr("disabled");
                                $(this).next().remove();
                                $(this).show();
                                window.location.reload();
                            });

                            $('#email_show').trigger('notify');
                        }, 2000);
                    }
                });

                $('#config-menus a').click(function (e) {
                    e.preventDefault();
                    $(this).tab('show');
                });

                // store the currently selected tab in the hash value
                $("ul.nav-pills > li > a").on("shown.bs.tab", function (e) {
                    window.location.hash = $(e.target).attr("href").substr(1);
                });

                // on load of the page: switch to the currently selected tab
                $('#config-menus a[href="' + window.location.hash + '"]').tab('show');

                $('a.resetConfig').confirm({
                    theme: 'dark',
                    title: gt('Reset Config to Defaults'),
                    content: gt('Are you sure you want to reset config to defaults?')
                });
            },

            general: {
                is_account_linked: '',

                init: function () {
                    SICKRAGE.root_dirs.init();

                    if ($("input[name='proxy_setting']").val().length === 0) {
                        $("input[id='proxy_indexers']").prop('checked', false);
                        $("label[for='proxy_indexers']").hide();
                    }

                    $("input[name='proxy_setting']").on('input', function () {
                        if ($(this).val().length === 0) {
                            $("input[id='proxy_indexers']").prop('checked', false);
                            $("label[for='proxy_indexers']").hide();
                        } else {
                            $("label[for='proxy_indexers']").show();
                        }
                    });

                    $(".viewIf").on('click', function () {
                        if ($(this).prop('checked')) {
                            $('.hide_if_' + $(this).attr('id')).css('display', 'none');
                            $('.show_if_' + $(this).attr('id')).fadeIn("fast", "linear");
                        } else {
                            $('.show_if_' + $(this).attr('id')).css('display', 'none');
                            $('.hide_if_' + $(this).attr('id')).fadeIn("fast", "linear");
                        }
                    });

                    $(".datePresets").on('click', function () {
                        var def = $('#date_presets').val();
                        if ($(this).prop('checked') && '%x' === def) {
                            def = '%a, %b %d, %Y';
                            $('#date_use_system_default').html('1');
                        } else if (!$(this).prop('checked') && '1' === $('#date_use_system_default').html()) {
                            def = '%x';
                        }

                        $('#date_presets').attr('name', 'date_preset_old');
                        $('#date_presets').attr('id', 'date_presets_old');

                        $('#date_presets_na').attr('name', 'date_preset');
                        $('#date_presets_na').attr('id', 'date_presets');

                        $('#date_presets_old').attr('name', 'date_preset_na');
                        $('#date_presets_old').attr('id', 'date_presets_na');

                        if (def) {
                            $('#date_presets').val(def);
                        }
                    });

                    $('#api_key').on('click', function () {
                        $('#api_key').select();
                    });

                    $("#generate_new_apikey").on('click', function () {
                        $.get(SICKRAGE.srWebRoot + '/config/general/generateApiKey',
                            function (data) {
                                if (data.error !== undefined) {
                                    alert(data.error);
                                    return;
                                }
                                $('#api_key').val(data);
                            });
                    });

                    $('#syncRemote').click(function () {
                        function updateProgress() {
                            $.getJSON(SICKRAGE.srWebRoot + '/googleDrive/getProgress', function (data) {
                                $('#current_info').html(data.current_info);
                            }).error(function () {
                                clearInterval(window.progressInterval);
                                $('#current_info').html('Uh oh, something went wrong');
                            });
                        }

                        $.ajax({
                            type: "GET",
                            url: SICKRAGE.srWebRoot + '/googleDrive/syncRemote',
                            beforeSend: function () {
                                window.progressInterval = setInterval(updateProgress, 100);
                                $('#pleaseWaitDialog').modal();
                            },
                            success: function () {
                                clearInterval(window.progressInterval);
                                $('#pleaseWaitDialog').modal('hide');
                            }
                        });
                    });

                    if ($('#pip3_path').length) {
                        $('#pip3_path').fileBrowser({
                            title: gt('Select path to pip3'),
                            key: 'pip3_path',
                            includeFiles: 1
                        });

                        $('#verifyPipPath').click(function () {
                            var pip3_path = $.trim($('#pip3_path').val());
                            if (!pip3_path) {
                                $('#testPIP-result').html(gt('Please fill out the necessary fields above.'));
                                $('#pip3_path').addClass('warning');
                                return;
                            }
                            $('#pip3_path').removeClass('warning');
                            $(this).prop('disabled', true);
                            $('#testPIP-result').html(SICKRAGE.loadingHTML);
                            $.get(SICKRAGE.srWebRoot + '/home/verifyPath', {
                                'path': pip3_path
                            }).done(function (data) {
                                $('#testPIP-result').html(data);
                                $('#verifyPipPath').prop('disabled', false);
                            });
                        });
                    }

                    if ($('#git_path').length) {
                        $('#git_path').fileBrowser({
                            title: gt('Select path to git'),
                            key: 'git_path',
                            includeFiles: 1
                        });

                        $('#verifyGitPath').click(function () {
                            var git_path = $.trim($('#git_path').val());
                            if (!git_path) {
                                $('#testGIT-result').html(gt('Please fill out the necessary fields above.'));
                                $('#git_path').addClass('warning');
                                return;
                            }
                            $('#git_path').removeClass('warning');
                            $(this).prop('disabled', true);
                            $('#testGIT-result').html(SICKRAGE.loadingHTML);
                            $.get(SICKRAGE.srWebRoot + '/home/verifyPath', {
                                'path': git_path
                            }).done(function (data) {
                                $('#testGIT-result').html(data);
                                $('#verifyGitPath').prop('disabled', false);
                            });
                        });
                    }

                    $('#installRequirements').on('click', function () {
                        window.location.href = SICKRAGE.srWebRoot + '/home/installRequirements';
                    });

                    $('#branchCheckout').on('click', function () {
                        window.location.href = SICKRAGE.srWebRoot + '/home/branchCheckout?branch=' + $("#branchVersion").val();
                    });

                    $("#web_auth_method").change(function () {
                        $(this).find("option:selected").each(function () {
                            const optionValue = $(this).val();
                            if (optionValue === 'local_auth') {
                                $('#content_use_local_auth').show();
                                $('#web_username').prop('required', true);
                                $('#web_password').prop('required', true);
                            } else {
                                $('#content_use_local_auth').hide();
                                $('#web_username').prop('required', false);
                                $('#web_password').prop('required', false);
                            }
                        });
                    }).change();

                    $('#link_sickrage_account').on('click', function () {
                        const pWindow = SICKRAGE.popupWindow(SICKRAGE.srWebRoot + '/account/link', 'Link SiCKRAGE Account', 1200, 650);
                        const timer = setInterval(function (pWindow) {
                            SICKRAGE.config.general.checkIsAccountLinked();
                            if (SICKRAGE.config.general.is_account_linked === 'true') {
                                pWindow.close();
                                clearInterval(timer);
                            }
                        }, 1000, pWindow);
                    });

                    $('#unlink_sickrage_account').on('click', function () {
                        const pWindow = SICKRAGE.popupWindow(SICKRAGE.srWebRoot + '/account/unlink', 'Unlink SiCKRAGE Account', 1200, 650);
                        const timer = setInterval(function (pWindow) {
                            SICKRAGE.config.general.checkIsAccountLinked();
                            if (SICKRAGE.config.general.is_account_linked === 'false') {
                                pWindow.close();
                                clearInterval(timer);
                            }
                        }, 1000, pWindow);
                    });
                },

                checkIsAccountLinked: function () {
                    $.ajax({
                        url: SICKRAGE.srWebRoot + '/account/is-linked',
                        dataType: 'json',
                        success: function (data) {
                            if (data.linked === 'true') {
                                $('#link_sickrage_account').addClass('d-none');
                                $('#unlink_sickrage_account').removeClass('d-none');
                            } else {
                                $('#unlink_sickrage_account').addClass('d-none');
                                $('#link_sickrage_account').removeClass('d-none');
                            }

                            SICKRAGE.config.general.is_account_linked = data.linked;
                        }
                    });
                }
            },

            subtitles: {
                init: function () {
                    $.getJSON(SICKRAGE.srWebRoot + '/config/subtitles/wanted_languages', function (result) {
                        new Tokenfield({
                            el: document.querySelector('#subtitles_languages'),
                            remote: {
                                url: SICKRAGE.srWebRoot + '/config/subtitles/get_code'
                            },
                            setItems: result,
                            itemName: 'subtitles_languages',
                            newitemName: 'subtitles_languages_new'
                        });
                    });

                    $('#subtitles_dir').fileBrowser({title: gt('Select Subtitles Download Directory')});

                    $('#editAService').change(function () {
                        SICKRAGE.config.subtitles.showHideServices();
                    });

                    $('.service_enabler').on('click', function () {
                        SICKRAGE.config.subtitles.refreshServiceList();
                    });

                    // initialization stuff
                    SICKRAGE.config.subtitles.showHideServices();

                    $("#service_order_list").sortable({
                        placeholder: 'ui-state-highlight',
                        update: function () {
                            SICKRAGE.config.subtitles.refreshServiceList();
                        }
                    });

                    $("#service_order_list").disableSelection();
                },

                showHideServices: function () {
                    $('.serviceDiv').each(function () {
                        var serviceName = $(this).attr('id');
                        var selectedService = $('#editAService :selected').val();

                        if (selectedService + 'Div' === serviceName) {
                            $(this).show();
                        } else {
                            $(this).hide();
                        }
                    });
                },

                addService: function (id, name, url, key, isDefault, showService) {
                    if (url.match('/$') === null) {
                        url = url + '/';
                    }

                    if ($('#service_order_list > #' + id).length === 0 && showService !== false) {
                        var toAdd = '<li class="ui-state-default" id="' + id + '"> <input type="checkbox" id="enable_' + id + '" class="service_enabler" CHECKED> <a href="' + SICKRAGE.anonURL + url + '" class="imgLink" target="_new"><img src="' + SICKRAGE.srWebRoot + '/images/providers/newznab.gif" alt="' + name + '" width="16" height="16"></a> ' + name + '</li>';

                        $('#service_order_list').append(toAdd);
                        $('#service_order_list').sortable("refresh");
                    }
                },

                deleteService: function (id) {
                    $('#service_order_list > #' + id).remove();
                },

                refreshServiceList: function () {
                    var idArr = $("#service_order_list").sortable('toArray');
                    var finalArr = [];
                    $.each(idArr, function (key, val) {
                        var checked = +$('#enable_' + val).prop('checked') ? '1' : '0';
                        finalArr.push(val + ':' + checked);
                    });
                    $("#service_order").val(finalArr.join(' '));
                }
            },

            search: {
                init: function () {
                    $('#nzb_method').change(SICKRAGE.config.search.nzbMethodHandler);
                    $('#torrent_method').change(SICKRAGE.config.search.torrentMethodHandler);

                    SICKRAGE.config.search.nzbMethodHandler();
                    SICKRAGE.config.search.torrentMethodHandler();

                    $('#testSABnzbd').click(function () {
                        $('#testSABnzbd_result').html(SICKRAGE.loadingHTML);
                        var sab_host = $('#sab_host').val();
                        var sab_username = $('#sab_username').val();
                        var sab_password = $('#sab_password').val();
                        var sab_apiKey = $('#sab_apikey').val();

                        $.get(SICKRAGE.srWebRoot + '/home/testSABnzbd', {
                                'host': sab_host,
                                'username': sab_username,
                                'password': sab_password,
                                'apikey': sab_apiKey
                            },
                            function (data) {
                                $('#testSABnzbd_result').html(data);
                            });
                    });

                    $('#testSynologyDSM').click(function () {
                        $('#testSynologyDSM_result').html(SICKRAGE.loadingHTML);
                        var nzb_method = $('#nzb_method').val();
                        var syno_dsm_host = $('#syno_dsm_host').val();
                        var syno_dsm_username = $('#syno_dsm_username').val();
                        var syno_dsm_password = $('#syno_dsm_password').val();

                        $.get(SICKRAGE.srWebRoot + '/home/testSynologyDSM', {
                                'nzb_method': nzb_method,
                                'host': syno_dsm_host,
                                'username': syno_dsm_username,
                                'password': syno_dsm_password
                            },
                            function (data) {
                                $('#testSynologyDSM_result').html(data);
                            });
                    });

                    $('#use_torrents').click(function () {
                        SICKRAGE.config.search.toggleTorrentTitle();
                    });

                    $('#test_torrent').click(function () {
                        $('#test_torrent_result').html(SICKRAGE.loadingHTML);
                        var torrent_method = $('#torrent_method :selected').val();
                        var torrent_host = $('#torrent_host').val();
                        var torrent_username = $('#torrent_username').val();
                        var torrent_password = $('#torrent_password').val();

                        $.get(SICKRAGE.srWebRoot + '/home/testTorrent', {
                                'torrent_method': torrent_method,
                                'host': torrent_host,
                                'username': torrent_username,
                                'password': torrent_password
                            },
                            function (data) {
                                $('#test_torrent_result').html(data);
                            });
                    });

                    SICKRAGE.config.search.rtorrentScgi();
                    $('#torrent_host').change(SICKRAGE.config.search.rtorrentScgi);

                    $('#nzb_dir').fileBrowser({title: gt('Select .nzb blackhole/watch location')});
                    $('#torrent_dir').fileBrowser({title: gt('Select .torrent blackhole/watch location')});
                    $('#torrent_path').fileBrowser({title: gt('Select .torrent download location')});
                },

                toggleTorrentTitle: function () {
                    if ($('#use_torrents').prop('checked')) {
                        $('#no_torrents').show();
                    } else {
                        $('#no_torrents').hide();
                    }
                },

                nzbMethodHandler: function () {
                    $('#blackhole_settings').hide();
                    $('#sabnzbd_settings').hide();
                    $('#nzbget_settings').hide();
                    $('#download_station_settings').hide();
                    $('#testSABnzbd').hide();
                    $('#testSABnzbd_result').hide();
                    $('#testSynologyDSM').hide();
                    $('#testSynologyDSM_result').hide();

                    $('#nzbget_host').prop('required', false);
                    $('#sab_host').prop('required', false);
                    $('#syno_dsm_host').prop('required', false);

                    var selectedProvider = $('#nzb_method').val();

                    if (selectedProvider.toLowerCase() !== 'blackhole') {
                        if (selectedProvider.toLowerCase() === 'nzbget') {
                            $('#nzbget_settings').show();
                            $('#nzbget_host').prop('required', true);
                        } else if (selectedProvider.toLowerCase() === 'sabnzbd') {
                            $('#sabnzbd_settings').show();
                            $('#testSABnzbd').show();
                            $('#testSABnzbd_result').show();
                            $('#sab_host').prop('required', true);
                        } else if (selectedProvider.toLowerCase() === 'download_station') {
                            $('#download_station_settings').show();
                            $('#testSynologyDSM').show();
                            $('#testSynologyDSM_result').show();
                            $('#syno_dsm_host').prop('required', true);
                        }
                    } else {
                        $('#blackhole_settings').show();
                        $('#nzbget_host').prop('required', false);
                        $('#sab_host').prop('required', false);
                        $('#syno_dsm_host').prop('required', false);
                    }
                },

                torrentMethodHandler: function () {
                    $('#options_torrent_clients').hide();
                    $('#options_torrent_blackhole').hide();
                    $('#torrent_host').prop('required', false);

                    var selectedProvider = $('#torrent_method').val(),
                        host = ' host:port',
                        username = ' username',
                        password = ' password',
                        client = '',
                        optionPanel = '#options_torrent_blackhole',
                        rpcurl = ' RPC URL';

                    // $('#torrent_method_icon').removeClass(function (index, css) {
                    //     return (css.match(/(^|\s)add-client-icon-\S+/g) || []).join(' ');
                    // });
                    // $('#torrent_method_icon').addClass('add-client-icon-' + selectedProvider.replace('_', '-'));

                    if (selectedProvider.toLowerCase() !== 'blackhole') {
                        $('#label_warning_deluge').hide();
                        $('#label_anime_warning_deluge').hide();
                        $('#torrent_verify_cert_option').hide();
                        $('#torrent_verify_deluge').hide();
                        $('#torrent_verify_rtorrent').hide();
                        $('#torrent_auth_type_option').hide();
                        $('#torrent_path_option').show();
                        $('#torrent_path_option').find('.fileBrowser').show();
                        $('#torrent_seed_time_option').hide();
                        $('#torrent_high_bandwidth_option').hide();
                        $('#torrent_label_option').show();
                        $('#torrent_label_anime_option').show();
                        $('#path_synology').hide();
                        $('#torrent_paused_option').show();
                        $('#torrent_rpcurl_option').hide();

                        if (selectedProvider.toLowerCase() === 'utorrent') {
                            client = 'uTorrent';
                            $('#torrent_path_option').hide();
                            $('#torrent_seed_time_label').text(gt('Minimum seeding time is'));
                            $('#torrent_seed_time_option').show();
                            $('#torrent_host').attr('placeholder', gt('URL to your uTorrent client (e.g. http://localhost:8000)'));
                            $('#torrent_host').prop('required', true);
                        } else if (selectedProvider.toLowerCase() === 'transmission') {
                            client = 'Transmission';
                            $('#torrent_seed_time_label').text(gt('Stop seeding when inactive for'));
                            $('#torrent_seed_time_option').show();
                            $('#torrent_high_bandwidth_option').show();
                            $('#torrent_label_option').hide();
                            $('#torrent_label_anime_option').hide();
                            $('#torrent_rpcurl_option').show();
                            $('#torrent_host').attr('placeholder', gt('URL to your Transmission client (e.g. http://localhost:9091)'));
                            $('#torrent_host').prop('required', true);
                        } else if (selectedProvider.toLowerCase() === 'deluge') {
                            client = 'Deluge';
                            $('#torrent_verify_cert_option').show();
                            $('#torrent_verify_deluge').show();
                            $('#torrent_verify_rtorrent').hide();
                            $('#label_warning_deluge').show();
                            $('#label_anime_warning_deluge').show();
                            $('#torrent_username_option').hide();
                            $('#torrent_username').prop('value', '');
                            $('#torrent_host').attr('placeholder', gt('URL to your Deluge client (e.g. http://localhost:8112)'));
                            $('#torrent_host').prop('required', true);
                        } else if (selectedProvider.toLowerCase() === 'deluged') {
                            client = 'Deluge';
                            $('#torrent_verify_cert_option').hide();
                            $('#torrent_verify_deluge').hide();
                            $('#torrent_verify_rtorrent').hide();
                            $('#label_warning_deluge').show();
                            $('#label_anime_warning_deluge').show();
                            $('#torrent_username_option').show();
                            $('#torrent_host').attr('placeholder', gt('IP or Hostname of your Deluge Daemon (e.g. scgi://localhost:58846)'));
                            $('#torrent_host').prop('required', true);
                        } else if (selectedProvider.toLowerCase() === 'download_station') {
                            client = 'Synology DS';
                            $('#torrent_label_option').hide();
                            $('#torrent_label_anime_option').hide();
                            $('#torrent_paused_option').hide();
                            $('#torrent_path_option').find('.fileBrowser').hide();
                            $('#torrent_host').attr('placeholder', gt('URL to your Synology DS client (e.g. http://localhost:5000)'));
                            $('#torrent_host').prop('required', true);
                            $('#path_synology').show();
                        } else if (selectedProvider.toLowerCase() === 'rtorrent') {
                            client = 'rTorrent';
                            $('#torrent_paused_option').hide();
                            $('#torrent_host').attr('placeholder', gt('URL to your rTorrent client (e.g. scgi://localhost:5000 or https://localhost/rutorrent/plugins/httprpc/action.php)'));
                            $('#torrent_verify_cert_option').show();
                            $('#torrent_verify_deluge').hide();
                            $('#torrent_verify_rtorrent').show();
                            $('#torrent_auth_type_option').show();
                            $('#torrent_host').prop('required', true);
                        } else if (selectedProvider.toLowerCase() === 'qbittorrent') {
                            client = 'qbittorrent';
                            $('#torrent_path_option').hide();
                            $('#label_warning_qbittorrent').show();
                            $('#label_anime_warning_qbittorrent').show();
                            $('#torrent_host').attr('placeholder', gt('URL to your qbittorrent client (e.g. http://localhost:8080)'));
                            $('#torrent_host').prop('required', true);
                        } else if (selectedProvider.toLowerCase() === 'mlnet') {
                            client = 'mlnet';
                            $('#torrent_path_option').hide();
                            $('#torrent_label_option').hide();
                            $('#torrent_verify_cert_option').hide();
                            $('#torrent_verify_deluge').hide();
                            $('#torrent_verify_rtorrent').hide();
                            $('#torrent_label_anime_option').hide();
                            $('#torrent_paused_option').hide();
                            $('#torrent_host').attr('placeholder', gt('URL to your MLDonkey (e.g. http://localhost:4080)'));
                            $('#torrent_host').prop('required', true);
                        } else if (selectedProvider.toLowerCase() === 'putio') {
                            client = 'putio';
                            $('#torrent_path_option').hide();
                            $('#torrent_label_option').hide();
                            $('#torrent_verify_cert_option').hide();
                            $('#torrent_verify_deluge').hide();
                            $('#torrent_verify_rtorrent').hide();
                            $('#torrent_label_anime_option').hide();
                            $('#torrent_paused_option').hide();
                            $('#torrent_host_option').hide();
                            $('#torrent_host').attr('placeholder', gt('URL to your putio client (e.g. http://localhost:8080)'));
                            $('#torrent_host').prop('required', true);
                        }

                        $('#host_title').text(client + host);
                        $('#username_title').text(client + username);
                        $('#password_title').text(client + password);
                        $('#torrent_client').text(client);
                        $('#rpcurl_title').text(client + rpcurl);

                        optionPanel = '#options_torrent_clients';
                    }

                    $(optionPanel).show();
                },

                rtorrentScgi: function () {
                    if ($('#torrent_method :selected').val().toLowerCase() === 'rtorrent') {
                        var hostname = $('#torrent_host').val();
                        var isMatch = hostname.substr(0, 7) === "scgi://";

                        if (isMatch) {
                            $('#torrent_username_option').hide();
                            $('#torrent_username').prop('value', '');
                            $('#torrent_password_option').hide();
                            $('#torrent_password').prop('value', '');
                            $('#torrent_auth_type_option').hide();
                            $("#torrent_auth_type option[value=none]").attr('selected', 'selected');
                        } else {
                            $('#torrent_username_option').show();
                            $('#torrent_password_option').show();
                            $('#torrent_auth_type_option').show();
                        }
                    }
                }
            },

            postprocessing: {
                init: function () {
                    $('#unpack').on('change', function () {
                        if ($(this).prop('checked')) {
                            SICKRAGE.config.postprocessing.israr_supported();
                        } else {
                            $('#unpack').tooltipster('close');
                        }
                    });

                    $('#name_presets').on('change', function () {
                        SICKRAGE.config.postprocessing.setup_naming();
                    });

                    $('#name_abd_presets').on('change', function () {
                        SICKRAGE.config.postprocessing.setup_abd_naming();
                    });

                    $('#naming_custom_abd').on('change', function () {
                        SICKRAGE.config.postprocessing.setup_abd_naming();
                    });

                    $('#name_sports_presets').on('change', function () {
                        SICKRAGE.config.postprocessing.setup_sports_naming();
                    });

                    $('#naming_custom_sports').on('change', function () {
                        SICKRAGE.config.postprocessing.setup_sports_naming();
                    });

                    $('#name_anime_presets').on('change', function () {
                        SICKRAGE.config.postprocessing.setup_anime_naming();
                    });

                    $('#naming_custom_anime').on('change', function () {
                        SICKRAGE.config.postprocessing.setup_anime_naming();
                    });

                    $('input[name="naming_anime"]').on('click', function () {
                        SICKRAGE.config.postprocessing.setup_anime_naming();
                    });

                    $('#naming_multi_ep').change(SICKRAGE.config.postprocessing.fill_examples);
                    $('#naming_pattern').focusout(SICKRAGE.config.postprocessing.fill_examples);
                    $('#naming_pattern').keyup(function () {
                        SICKRAGE.config.postprocessing.typewatch(function () {
                            SICKRAGE.config.postprocessing.fill_examples();
                        }, 500);
                    });

                    $('#naming_anime_multi_ep').change(SICKRAGE.config.postprocessing.fill_anime_examples);
                    $('#naming_anime_pattern').focusout(SICKRAGE.config.postprocessing.fill_anime_examples);
                    $('#naming_anime_pattern').keyup(function () {
                        SICKRAGE.config.postprocessing.typewatch(function () {
                            SICKRAGE.config.postprocessing.fill_anime_examples();
                        }, 500);
                    });

                    $('#naming_abd_pattern').focusout(SICKRAGE.config.postprocessing.fill_examples);
                    $('#naming_abd_pattern').keyup(function () {
                        SICKRAGE.config.postprocessing.typewatch(function () {
                            SICKRAGE.config.postprocessing.fill_abd_examples();
                        }, 500);
                    });

                    $('#naming_sports_pattern').focusout(SICKRAGE.config.postprocessing.fill_examples);
                    $('#naming_sports_pattern').keyup(function () {
                        SICKRAGE.config.postprocessing.typewatch(function () {
                            SICKRAGE.config.postprocessing.fill_sports_examples();
                        }, 500);
                    });

                    $('#naming_anime_pattern').focusout(SICKRAGE.config.postprocessing.fill_examples);
                    $('#naming_anime_pattern').keyup(function () {
                        SICKRAGE.config.postprocessing.typewatch(function () {
                            SICKRAGE.config.postprocessing.fill_anime_examples();
                        }, 500);
                    });

                    $('#show_naming_key').on('click', function () {
                        $('#naming_key').toggleClass('d-none');
                    });
                    $('#show_naming_abd_key').on('click', function () {
                        $('#naming_abd_key').toggleClass('d-none');
                    });
                    $('#show_naming_sports_key').on('click', function () {
                        $('#naming_sports_key').toggleClass('d-none');
                    });
                    $('#show_naming_anime_key').on('click', function () {
                        $('#naming_anime_key').toggleClass('d-none');
                    });
                    $('#do_custom').on('click', function () {
                        $('#naming_pattern').val($('#name_presets :selected').attr('id'));
                        $('#naming_custom').show();
                        $('#naming_pattern').focus();
                    });

                    SICKRAGE.config.postprocessing.setup_naming();
                    SICKRAGE.config.postprocessing.setup_abd_naming();
                    SICKRAGE.config.postprocessing.setup_sports_naming();
                    SICKRAGE.config.postprocessing.setup_anime_naming();

                    // -- start of metadata options div toggle code --
                    $('#metadataType').on('change keyup', function () {
                        SICKRAGE.config.postprocessing.showHideMetadata();
                    });

                    //initialize to show the div
                    SICKRAGE.config.postprocessing.showHideMetadata();
                    // -- end of metadata options div toggle code --

                    $('.metadata_checkbox').on('click', function () {
                        SICKRAGE.config.postprocessing.refreshMetadataConfig(false);
                    });

                    SICKRAGE.config.postprocessing.refreshMetadataConfig(true);

                    $('img[title]').tooltipster({
                        position: {
                            viewport: $(window),
                            at: 'bottom center',
                            my: 'top right'
                        }
                    });

                    $('i[title]').tooltipster({
                        position: {
                            viewport: $(window),
                            at: 'top center',
                            my: 'bottom center'
                        }
                    });

                    $('.custom-pattern,#unpack').tooltipster('content', gt('validating...'));
                    $('#tv_download_dir').fileBrowser({title: gt('Select TV Download Directory')});
                    $('#unpack_dir').fileBrowser({title: gt('Select UNPACK Directory')});
                },

                typewatch: function () {
                    var timer = 0;
                    return function (callback, ms) {
                        clearTimeout(timer);
                        timer = setTimeout(callback, ms);
                    };
                },

                israr_supported: function () {
                    $.get(SICKRAGE.srWebRoot + '/config/postProcessing/isRarSupported', function (data) {
                        if (data !== "supported") {
                            $('#unpack').tooltipster('content', gt('Unrar Executable not found.'));
                            $('#unpack').tooltipster('open');
                            $('#unpack').css('background-color', '#FFFFDD');
                        }
                    });
                },

                fill_examples: function () {
                    var pattern = $('#naming_pattern').val();
                    var multi = $('#naming_multi_ep :selected').val();
                    var anime_type = $('input[name="naming_anime"]:checked').val();

                    $.get(SICKRAGE.srWebRoot + '/config/postProcessing/testNaming', {
                        pattern: pattern,
                        anime_type: 3
                    }, function (data) {
                        if (data) {
                            $('#naming_example').text(data + '.ext');
                            $('#naming_example_div').show();
                        } else {
                            $('#naming_example_div').hide();
                        }
                    });

                    $.get(SICKRAGE.srWebRoot + '/config/postProcessing/testNaming', {
                        pattern: pattern,
                        multi: multi,
                        anime_type: 3
                    }, function (data) {
                        if (data) {
                            $('#naming_example_multi').text(data + '.ext');
                            $('#naming_example_multi_div').show();
                        } else {
                            $('#naming_example_multi_div').hide();
                        }
                    });

                    $.get(SICKRAGE.srWebRoot + '/config/postProcessing/isNamingValid', {
                        pattern: pattern,
                        multi: multi,
                        anime_type: anime_type
                    }, function (data) {
                        if (data === "invalid") {
                            $('#naming_pattern').tooltipster('content', gt('This pattern is invalid.'));
                            $('#naming_pattern').tooltipster('open');
                            $('#naming_pattern').css('background-color', '#FFDDDD');
                        } else if (data === "seasonfolders") {
                            $('#naming_pattern').tooltipster('content', gt('This pattern would be invalid without the folders, using it will force "Flatten" off for all shows.'));
                            $('#naming_pattern').tooltipster('open');
                            $('#naming_pattern').css('background-color', '#FFFFDD');
                        } else {
                            $('#naming_pattern').tooltipster('content', gt('This pattern is valid.'));
                            $('#naming_pattern').tooltipster('close');
                            $('#naming_pattern').css('background-color', '#FFFFFF');
                        }
                    });
                },

                fill_abd_examples: function () {
                    var pattern = $('#naming_abd_pattern').val();

                    $.get(SICKRAGE.srWebRoot + '/config/postProcessing/testNaming', {
                        pattern: pattern,
                        abd: 'True'
                    }, function (data) {
                        if (data) {
                            $('#naming_abd_example').text(data + '.ext');
                            $('#naming_abd_example_div').show();
                        } else {
                            $('#naming_abd_example_div').hide();
                        }
                    });

                    $.get(SICKRAGE.srWebRoot + '/config/postProcessing/isNamingValid', {
                        pattern: pattern,
                        abd: 'True'
                    }, function (data) {
                        if (data === "invalid") {
                            $('#naming_abd_pattern').tooltipster('content', gt('This pattern is invalid.'));
                            $('#naming_abd_pattern').tooltipster('open');
                            $('#naming_abd_pattern').css('background-color', '#FFDDDD');
                        } else if (data === "seasonfolders") {
                            $('#naming_abd_pattern').tooltipster('content', gt('This pattern would be invalid without the folders, using it will force "Flatten" off for all shows.'));
                            $('#naming_abd_pattern').tooltipster('open');
                            $('#naming_abd_pattern').css('background-color', '#FFFFDD');
                        } else {
                            $('#naming_abd_pattern').tooltipster('content', gt('This pattern is valid.'));
                            $('#naming_abd_pattern').tooltipster('close');
                            $('#naming_abd_pattern').css('background-color', '#FFFFFF');
                        }
                    });
                },

                fill_sports_examples: function () {
                    var pattern = $('#naming_sports_pattern').val();

                    $.get(SICKRAGE.srWebRoot + '/config/postProcessing/testNaming', {
                        pattern: pattern,
                        sports: 'True'
                    }, function (data) {
                        if (data) {
                            $('#naming_sports_example').text(data + '.ext');
                            $('#naming_sports_example_div').show();
                        } else {
                            $('#naming_sports_example_div').hide();
                        }
                    });

                    $.get(SICKRAGE.srWebRoot + '/config/postProcessing/isNamingValid', {
                        pattern: pattern,
                        sports: 'True'
                    }, function (data) {
                        if (data === "invalid") {
                            $('#naming_sports_pattern').tooltipster('content', gt('This pattern is invalid.'));
                            $('#naming_sports_pattern').tooltipster('open');
                            $('#naming_sports_pattern').css('background-color', '#FFDDDD');
                        } else if (data === "seasonfolders") {
                            $('#naming_sports_pattern').tooltipster('content', gt('This pattern would be invalid without the folders, using it will force "Flatten" off for all shows.'));
                            $('#naming_sports_pattern').tooltipster('open');
                            $('#naming_sports_pattern').css('background-color', '#FFFFDD');
                        } else {
                            $('#naming_sports_pattern').tooltipster('content', gt('This pattern is valid.'));
                            $('#naming_sports_pattern').tooltipster('close');
                            $('#naming_sports_pattern').css('background-color', '#FFFFFF');
                        }
                    });
                },

                fill_anime_examples: function () {
                    var pattern = $('#naming_anime_pattern').val();
                    var multi = $('#naming_anime_multi_ep :selected').val();
                    var anime_type = $('input[name="naming_anime"]:checked').val();

                    $.get(SICKRAGE.srWebRoot + '/config/postProcessing/testNaming', {
                        pattern: pattern,
                        anime_type: anime_type
                    }, function (data) {
                        if (data) {
                            $('#naming_example_anime').text(data + '.ext');
                            $('#naming_example_anime_div').show();
                        } else {
                            $('#naming_example_anime_div').hide();
                        }
                    });

                    $.get(SICKRAGE.srWebRoot + '/config/postProcessing/testNaming', {
                        pattern: pattern,
                        multi: multi,
                        anime_type: anime_type
                    }, function (data) {
                        if (data) {
                            $('#naming_example_multi_anime').text(data + '.ext');
                            $('#naming_example_multi_anime_div').show();
                        } else {
                            $('#naming_example_multi_anime_div').hide();
                        }
                    });

                    $.get(SICKRAGE.srWebRoot + '/config/postProcessing/isNamingValid', {
                        pattern: pattern,
                        multi: multi,
                        anime_type: anime_type
                    }, function (data) {
                        if (data === "invalid") {
                            $('#naming_pattern').tooltipster('content', gt('This pattern is invalid.'));
                            $('#naming_pattern').tooltipster('open');
                            $('#naming_pattern').css('background-color', '#FFDDDD');
                        } else if (data === "seasonfolders") {
                            $('#naming_pattern').tooltipster('content', gt('This pattern would be invalid without the folders, using it will force "Flatten" off for all shows.'));
                            //$('#naming_pattern').tooltipster('open');
                            $('#naming_pattern').css('background-color', '#FFFFDD');
                        } else {
                            $('#naming_pattern').tooltipster('content', gt('This pattern is valid.'));
                            $('#naming_pattern').tooltipster('close');
                            $('#naming_pattern').css('background-color', '#FFFFFF');
                        }
                    });
                },

                setup_naming: function () {
                    // if it is a custom selection then show the text box
                    if ($('#name_presets :selected').val() === "Custom...") {
                        $('#naming_custom').show();
                    } else {
                        $('#naming_custom').hide();
                        $('#naming_pattern').val($('#name_presets :selected').attr('id'));
                    }
                    SICKRAGE.config.postprocessing.fill_examples();
                },

                setup_abd_naming: function () {
                    // if it is a custom selection then show the text box
                    if ($('#name_abd_presets :selected').val() === "Custom...") {
                        $('#naming_abd_custom').show();
                    } else {
                        $('#naming_abd_custom').hide();
                        $('#naming_abd_pattern').val($('#name_abd_presets :selected').attr('id'));
                    }
                    SICKRAGE.config.postprocessing.fill_abd_examples();
                },

                setup_sports_naming: function () {
                    // if it is a custom selection then show the text box
                    if ($('#name_sports_presets :selected').val() === "Custom...") {
                        $('#naming_sports_custom').show();
                    } else {
                        $('#naming_sports_custom').hide();
                        $('#naming_sports_pattern').val($('#name_sports_presets :selected').attr('id'));
                    }
                    SICKRAGE.config.postprocessing.fill_sports_examples();
                },

                setup_anime_naming: function () {
                    // if it is a custom selection then show the text box
                    if ($('#name_anime_presets :selected').val() === "Custom...") {
                        $('#naming_anime_custom').show();
                    } else {
                        $('#naming_anime_custom').hide();
                        $('#naming_anime_pattern').val($('#name_anime_presets :selected').attr('id'));
                    }
                    SICKRAGE.config.postprocessing.fill_anime_examples();
                },

                showHideMetadata: function () {
                    $('.metadataDiv').each(function () {
                        var targetName = $(this).attr('id');
                        var selectedTarget = $('#metadataType :selected').val();

                        if (selectedTarget === targetName) {
                            $(this).show();
                        } else {
                            $(this).hide();
                        }
                    });
                },

                refreshMetadataConfig: function (first) {
                    var cur_most = 0;
                    var cur_most_provider = '';

                    $('.metadataDiv').each(function () {
                        var generator_name = $(this).attr('id');

                        var config_arr = [];
                        var show_metadata = $("#" + generator_name + "_show_metadata").prop('checked');
                        var episode_metadata = $("#" + generator_name + "_episode_metadata").prop('checked');
                        var fanart = $("#" + generator_name + "_fanart").prop('checked');
                        var poster = $("#" + generator_name + "_poster").prop('checked');
                        var banner = $("#" + generator_name + "_banner").prop('checked');
                        var episode_thumbnails = $("#" + generator_name + "_episode_thumbnails").prop('checked');
                        var season_posters = $("#" + generator_name + "_season_posters").prop('checked');
                        var season_banners = $("#" + generator_name + "_season_banners").prop('checked');
                        var season_all_poster = $("#" + generator_name + "_season_all_poster").prop('checked');
                        var season_all_banner = $("#" + generator_name + "_season_all_banner").prop('checked');
                        var enabled = $("#" + generator_name + "_enabled").prop('checked');

                        config_arr.push(show_metadata ? '1' : '0');
                        config_arr.push(episode_metadata ? '1' : '0');
                        config_arr.push(fanart ? '1' : '0');
                        config_arr.push(poster ? '1' : '0');
                        config_arr.push(banner ? '1' : '0');
                        config_arr.push(episode_thumbnails ? '1' : '0');
                        config_arr.push(season_posters ? '1' : '0');
                        config_arr.push(season_banners ? '1' : '0');
                        config_arr.push(season_all_poster ? '1' : '0');
                        config_arr.push(season_all_banner ? '1' : '0');
                        config_arr.push(enabled ? '1' : '0');

                        var cur_num = 0;
                        for (var i = 0; i < config_arr.length; i++) {
                            cur_num += parseInt(config_arr[i]);
                        }
                        if (cur_num > cur_most) {
                            cur_most = cur_num;
                            cur_most_provider = generator_name;
                        }

                        $("#" + generator_name + "_eg_show_metadata").attr('class', show_metadata ? 'enabled' : 'disabled');
                        $("#" + generator_name + "_eg_episode_metadata").attr('class', episode_metadata ? 'enabled' : 'disabled');
                        $("#" + generator_name + "_eg_fanart").attr('class', fanart ? 'enabled' : 'disabled');
                        $("#" + generator_name + "_eg_poster").attr('class', poster ? 'enabled' : 'disabled');
                        $("#" + generator_name + "_eg_banner").attr('class', banner ? 'enabled' : 'disabled');
                        $("#" + generator_name + "_eg_episode_thumbnails").attr('class', episode_thumbnails ? 'enabled' : 'disabled');
                        $("#" + generator_name + "_eg_season_posters").attr('class', season_posters ? 'enabled' : 'disabled');
                        $("#" + generator_name + "_eg_season_banners").attr('class', season_banners ? 'enabled' : 'disabled');
                        $("#" + generator_name + "_eg_season_all_poster").attr('class', season_all_poster ? 'enabled' : 'disabled');
                        $("#" + generator_name + "_eg_season_all_banner").attr('class', season_all_banner ? 'enabled' : 'disabled');
                        $("#" + generator_name + "_data").val(config_arr.join('|'));

                    });

                    if (cur_most_provider !== '' && first) {
                        $('#metadataType option[value=' + cur_most_provider + ']').attr('selected', 'selected');
                        SICKRAGE.config.postprocessing.showHideMetadata();
                    }
                }
            },

            notifications: {
                init: function () {
                    $('#testGrowl').click(function () {
                        var growl_host = $.trim($('#growl_host').val());
                        var growl_password = $.trim($('#growl_password').val());
                        if (!growl_host) {
                            $('#testGrowl-result').html(gt('Please fill out the necessary fields above.'));
                            $('#growl_host').addClass('warning');
                            return;
                        }
                        $('#growl_host').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testGrowl-result').html(SICKRAGE.loadingHTML);
                        $.get(SICKRAGE.srWebRoot + '/home/testGrowl', {'host': growl_host, 'password': growl_password})
                            .done(function (data) {
                                $('#testGrowl-result').html(data);
                                $('#testGrowl').prop('disabled', false);
                            });
                    });

                    $('#testProwl').click(function () {
                        var prowl_api = $.trim($('#prowl_api').val());
                        var prowl_priority = $('#prowl_priority').val();
                        if (!prowl_api) {
                            $('#testProwl-result').html(gt('Please fill out the necessary fields above.'));
                            $('#prowl_api').addClass('warning');
                            return;
                        }
                        $('#prowl_api').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testProwl-result').html(SICKRAGE.loadingHTML);
                        $.get(SICKRAGE.srWebRoot + '/home/testProwl', {
                            'prowl_api': prowl_api,
                            'prowl_priority': prowl_priority
                        }).done(function (data) {
                            $('#testProwl-result').html(data);
                            $('#testProwl').prop('disabled', false);
                        });
                    });

                    $('#testKODI').click(function () {
                        var kodi_host = $.trim($('#kodi_host').val());
                        var kodi_username = $.trim($('#kodi_username').val());
                        var kodi_password = $.trim($('#kodi_password').val());
                        if (!kodi_host) {
                            $('#testKODI-result').html(gt('Please fill out the necessary fields above.'));
                            $('#kodi_host').addClass('warning');
                            return;
                        }
                        $('#kodi_host').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testKODI-result').html(SICKRAGE.loadingHTML);
                        $.get(SICKRAGE.srWebRoot + '/home/testKODI', {
                            'host': kodi_host,
                            'username': kodi_username,
                            'password': kodi_password
                        }).done(function (data) {
                            $('#testKODI-result').html(data);
                            $('#testKODI').prop('disabled', false);
                        });
                    });

                    $('#testPMC').click(function () {
                        var plex_host = $.trim($('#plex_host').val());
                        var plex_client_username = $.trim($('#plex_client_username').val());
                        var plex_client_password = $.trim($('#plex_client_password').val());
                        if (!plex_host) {
                            $('#testPMC-result').html(gt('Please fill out the necessary fields above.'));
                            $('#plex_host').addClass('warning');
                            return;
                        }
                        $('#plex_host').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testPMC-result').html(SICKRAGE.loadingHTML);
                        $.get(SICKRAGE.srWebRoot + '/home/testPMC', {
                            'host': plex_host,
                            'username': plex_client_username,
                            'password': plex_client_password
                        }).done(function (data) {
                            $('#testPMC-result').html(data);
                            $('#testPMC').prop('disabled', false);
                        });
                    });

                    $('#testPMS').click(function () {
                        var plex_server_host = $.trim($('#plex_server_host').val());
                        var plex_username = $.trim($('#plex_username').val());
                        var plex_password = $.trim($('#plex_password').val());
                        var plex_server_token = $.trim($('#plex_server_token').val());
                        if (!plex_server_host) {
                            $('#testPMS-result').html(gt('Please fill out the necessary fields above.'));
                            $('#plex_server_host').addClass('warning');
                            return;
                        }
                        $('#plex_server_host').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testPMS-result').html(SICKRAGE.loadingHTML);
                        $.get(SICKRAGE.srWebRoot + '/home/testPMS', {
                            'host': plex_server_host,
                            'username': plex_username,
                            'password': plex_password,
                            'plex_server_token': plex_server_token
                        }).done(function (data) {
                            $('#testPMS-result').html(data);
                            $('#testPMS').prop('disabled', false);
                        });
                    });

                    $('#testEMBY').click(function () {
                        var emby_host = $('#emby_host').val();
                        var emby_apikey = $('#emby_apikey').val();
                        if (!emby_host || !emby_apikey) {
                            $('#testEMBY-result').html(gt('Please fill out the necessary fields above.'));
                            if (!emby_host) {
                                $('#emby_host').addClass('warning');
                            } else {
                                $('#emby_host').removeClass('warning');
                            }
                            if (!emby_apikey) {
                                $('#emby_apikey').addClass('warning');
                            } else {
                                $('#emby_apikey').removeClass('warning');
                            }
                            return;
                        }
                        $('#emby_host,#emby_apikey').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testEMBY-result').html(SICKRAGE.loadingHTML);
                        $.get(SICKRAGE.srWebRoot + '/home/testEMBY', {
                            'host': emby_host,
                            'emby_apikey': emby_apikey
                        }).done(function (data) {
                            $('#testEMBY-result').html(data);
                            $('#testEMBY').prop('disabled', false);
                        });
                    });

                    $('#testBoxcar2').click(function () {
                        var boxcar2_accesstoken = $.trim($('#boxcar2_accesstoken').val());
                        if (!boxcar2_accesstoken) {
                            $('#testBoxcar2-result').html(gt('Please fill out the necessary fields above.'));
                            $('#boxcar2_accesstoken').addClass('warning');
                            return;
                        }
                        $('#boxcar2_accesstoken').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testBoxcar2-result').html(SICKRAGE.loadingHTML);
                        $.get(SICKRAGE.srWebRoot + '/home/testBoxcar2', {'accesstoken': boxcar2_accesstoken}).done(function (data) {
                            $('#testBoxcar2-result').html(data);
                            $('#testBoxcar2').prop('disabled', false);
                        });
                    });

                    $('#testPushover').click(function () {
                        var pushover_userkey = $('#pushover_userkey').val();
                        var pushover_apikey = $('#pushover_apikey').val();
                        if (!pushover_userkey || !pushover_apikey) {
                            $('#testPushover-result').html(gt('Please fill out the necessary fields above.'));
                            if (!pushover_userkey) {
                                $('#pushover_userkey').addClass('warning');
                            } else {
                                $('#pushover_userkey').removeClass('warning');
                            }
                            if (!pushover_apikey) {
                                $('#pushover_apikey').addClass('warning');
                            } else {
                                $('#pushover_apikey').removeClass('warning');
                            }
                            return;
                        }
                        $('#pushover_userkey,#pushover_apikey').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testPushover-result').html(SICKRAGE.loadingHTML);
                        $.get(SICKRAGE.srWebRoot + '/home/testPushover', {
                            'userKey': pushover_userkey,
                            'apiKey': pushover_apikey
                        }).done(function (data) {
                            $('#testPushover-result').html(data);
                            $('#testPushover').prop('disabled', false);
                        });
                    });

                    $('#testLibnotify').click(function () {
                        $('#testLibnotify-result').html(SICKRAGE.loadingHTML);
                        $.get(SICKRAGE.srWebRoot + '/home/testLibnotify', function (data) {
                            $('#testLibnotify-result').html(data);
                        });
                    });

                    $('#twitterStep1').click(function () {
                        $('#testTwitter-result').html(SICKRAGE.loadingHTML);
                        $.get(SICKRAGE.srWebRoot + '/home/twitterStep1', function (data) {
                            window.open(data);
                        }).done(function () {
                            $('#testTwitter-result').html(gt('<b>Step1:</b> Confirm Authorization'));
                        });
                    });

                    $('#twitterStep2').click(function () {
                        var twitter_key = $.trim($('#twitter_key').val());
                        if (!twitter_key) {
                            $('#testTwitter-result').html(gt('Please fill out the necessary fields above.'));
                            $('#twitter_key').addClass('warning');
                            return;
                        }
                        $('#twitter_key').removeClass('warning');
                        $('#testTwitter-result').html(SICKRAGE.loadingHTML);
                        $.get(SICKRAGE.srWebRoot + '/home/twitterStep2', {'key': twitter_key}, function (data) {
                            $('#testTwitter-result').html(data);
                        });
                    });

                    $('#testTwitter').click(function () {
                        $.get(SICKRAGE.srWebRoot + '/home/testTwitter', function (data) {
                            $('#testTwitter-result').html(data);
                        });
                    });

                    $('#testTwilio').on('click', function () {
                        var twilio_account_sid = $.trim($('#twilio_account_sid').val());
                        var twilio_phone_sid = $.trim($('#twilio_phone_sid').val());
                        var twilio_auth_token = $.trim($('#twilio_auth_token').val());
                        var twilio_to_number = $.trim($('#twilio_to_number').val());

                        $(this).prop('disabled', true);
                        $('#testTwilio-result').html(SICKRAGE.loadingHTML);
                        $.get(SICKRAGE.srWebRoot + '/home/testTwilio', {
                            'account_sid': twilio_account_sid,
                            'phone_sid': twilio_phone_sid,
                            'auth_token': twilio_auth_token,
                            'to_number': twilio_to_number
                        }).done(function (data) {
                            $('#testTwilio-result').html(data);
                            $('#testTwilio').prop('disabled', false);
                        });
                    });

                    $('#testSlack').on('click', function () {
                        $.get(SICKRAGE.srWebRoot + '/home/testSlack', function (data) {
                            $('#testSlack-result').html(data);
                        });
                    });

                    $('#testDiscord').on('click', function () {
                        $.get(SICKRAGE.srWebRoot + '/home/testDiscord', function (data) {
                            $('#testDiscord-result').html(data);
                        });
                    });

                    $('#settingsNMJ').click(function () {
                        if (!$('#nmj_host').val()) {
                            alert(gt('Please fill in the Popcorn IP address'));
                            $('#nmj_host').focus();
                            return;
                        }
                        $('#testNMJ-result').html(SICKRAGE.loadingHTML);
                        var nmj_host = $('#nmj_host').val();

                        $.get(SICKRAGE.srWebRoot + '/home/settingsNMJ', {'host': nmj_host}, function (data) {
                            if (data === null) {
                                $('#nmj_database').removeAttr('readonly');
                                $('#nmj_mount').removeAttr('readonly');
                            }
                            var JSONData = $.parseJSON(data);
                            $('#testNMJ-result').html(JSONData.message);
                            $('#nmj_database').val(JSONData.database);
                            $('#nmj_mount').val(JSONData.mount);

                            if (JSONData.database) {
                                $('#nmj_database').attr('readonly', true);
                            } else {
                                $('#nmj_database').removeAttr('readonly');
                            }
                            if (JSONData.mount) {
                                $('#nmj_mount').attr('readonly', true);
                            } else {
                                $('#nmj_mount').removeAttr('readonly');
                            }
                        });
                    });

                    $('#testNMJ').click(function () {
                        var nmj_host = $.trim($('#nmj_host').val());
                        var nmj_database = $('#nmj_database').val();
                        var nmj_mount = $('#nmj_mount').val();
                        if (!nmj_host) {
                            $('#testNMJ-result').html(gt('Please fill out the necessary fields above.'));
                            $('#nmj_host').addClass('warning');
                            return;
                        }
                        $('#nmj_host').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testNMJ-result').html(SICKRAGE.loadingHTML);
                        $.get(SICKRAGE.srWebRoot + '/home/testNMJ', {
                            'host': nmj_host,
                            'database': nmj_database,
                            'mount': nmj_mount
                        }).done(function (data) {
                            $('#testNMJ-result').html(data);
                            $('#testNMJ').prop('disabled', false);
                        });
                    });

                    $('#settingsNMJv2').click(function () {
                        if (!$('#nmjv2_host').val()) {
                            alert(gt('Please fill in the Popcorn IP address'));
                            $('#nmjv2_host').focus();
                            return;
                        }
                        $('#testNMJv2-result').html(SICKRAGE.loadingHTML);
                        var nmjv2_host = $('#nmjv2_host').val();
                        var nmjv2_dbloc;
                        var radios = document.getElementsByName('nmjv2_dbloc');
                        for (var i = 0; i < radios.length; i++) {
                            if (radios[i].checked) {
                                nmjv2_dbloc = radios[i].value;
                                break;
                            }
                        }

                        var nmjv2_dbinstance = $('#NMJv2db_instance').val();
                        $.get(SICKRAGE.srWebRoot + '/home/settingsNMJv2', {
                            'host': nmjv2_host,
                            'dbloc': nmjv2_dbloc,
                            'instance': nmjv2_dbinstance
                        }, function (data) {
                            if (data === null) {
                                $('#nmjv2_database').removeAttr('readonly');
                            }
                            var JSONData = $.parseJSON(data);
                            $('#testNMJv2-result').html(JSONData.message);
                            $('#nmjv2_database').val(JSONData.database);

                            if (JSONData.database) {
                                $('#nmjv2_database').attr('readonly', true);
                            } else {
                                $('#nmjv2_database').removeAttr('readonly');
                            }
                        });
                    });

                    $('#testNMJv2').click(function () {
                        var nmjv2_host = $.trim($('#nmjv2_host').val());
                        if (!nmjv2_host) {
                            $('#testNMJv2-result').html(gt('Please fill out the necessary fields above.'));
                            $('#nmjv2_host').addClass('warning');
                            return;
                        }
                        $('#nmjv2_host').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testNMJv2-result').html(SICKRAGE.loadingHTML);
                        $.get(SICKRAGE.srWebRoot + '/home/testNMJv2', {'host': nmjv2_host}).done(function (data) {
                            $('#testNMJv2-result').html(data);
                            $('#testNMJv2').prop('disabled', false);
                        });
                    });

                    $('#testFreeMobile').click(function () {
                        var freemobile_id = $.trim($('#freemobile_id').val());
                        var freemobile_apikey = $.trim($('#freemobile_apikey').val());
                        if (!freemobile_id || !freemobile_apikey) {
                            $('#testFreeMobile-result').html(gt('Please fill out the necessary fields above.'));
                            if (!freemobile_id) {
                                $('#freemobile_id').addClass('warning');
                            } else {
                                $('#freemobile_id').removeClass('warning');
                            }
                            if (!freemobile_apikey) {
                                $('#freemobile_apikey').addClass('warning');
                            } else {
                                $('#freemobile_apikey').removeClass('warning');
                            }
                            return;
                        }
                        $('#freemobile_id,#freemobile_apikey').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testFreeMobile-result').html(SICKRAGE.loadingHTML);
                        $.get(SICKRAGE.srWebRoot + '/home/testFreeMobile', {
                            'freemobile_id': freemobile_id,
                            'freemobile_apikey': freemobile_apikey
                        }).done(function (data) {
                            $('#testFreeMobile-result').html(data);
                            $('#testFreeMobile').prop('disabled', false);
                        });
                    });

                    $('#testTelegram').on('click', function () {
                        var telegram = {};
                        telegram.id = $.trim($('#telegram_id').val());
                        telegram.apikey = $.trim($('#telegram_apikey').val());
                        if (!telegram.id || !telegram.apikey) {
                            $('#testTelegram-result').html(gt('Please fill out the necessary fields above.'));
                            if (!telegram.id) {
                                $('#telegram_id').addClass('warning');
                            } else {
                                $('#telegram_id').removeClass('warning');
                            }
                            if (!telegram.apikey) {
                                $('#telegram_apikey').addClass('warning');
                            } else {
                                $('#telegram_apikey').removeClass('warning');
                            }
                            return;
                        }
                        $('#telegram_id,#telegram_apikey').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testTelegram-result').html(SICKRAGE.loadingHTML);
                        $.get(SICKRAGE.srWebRoot + '/home/testTelegram', {
                            'telegram_id': telegram.id,
                            'telegram_apikey': telegram.apikey
                        }).done(function (data) {
                            $('#testTelegram-result').html(data);
                            $('#testTelegram').prop('disabled', false);
                        });
                    });

                    $('#testJoin').on('click', function () {
                        var join = {};
                        join.id = $.trim($('#join_id').val());
                        join.apikey = $.trim($('#join_apikey').val());
                        if (!join.id || !join.apikey) {
                            $('#testJoin-result').html(gt('Please fill out the necessary fields above.'));
                            if (!join.id) {
                                $('#join_id').addClass('warning');
                            } else {
                                $('#join_id').removeClass('warning');
                            }
                            if (!join.apikey) {
                                $('#join_apikey').addClass('warning');
                            } else {
                                $('#join_apikey').removeClass('warning');
                            }
                            return;
                        }
                        $('#join_id,#join_apikey').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testJoin-result').html(SICKRAGE.loadingHTML);
                        $.get(SICKRAGE.srWebRoot + '/home/testJoin', {
                            'join_id': join.id,
                            'join_apikey': join.apikey
                        }).done(function (data) {
                            $('#testJoin-result').html(data);
                            $('#testJoin').prop('disabled', false);
                        });
                    });

                    $('#TraktGetPin').click(function () {
                        window.open($('#trakt_pin_url').val(), "popUp", "toolbar=no, scrollbars=no, resizable=no, top=200, left=200, width=650, height=550");
                        $('#trakt_pin').removeClass('d-none');
                    });

                    $('#trakt_pin').on('keyup change', function () {
                        if ($('#trakt_pin').val().length !== 0) {
                            $('#TraktGetPin').addClass('d-none');
                            $('#authTrakt').removeClass('d-none');
                        } else {
                            $('#TraktGetPin').removeClass('d-none');
                            $('#authTrakt').addClass('d-none');
                        }
                    });

                    $('#authTrakt').click(function () {
                        if ($('#trakt_pin').val().length !== 0) {
                            $.get(SICKRAGE.srWebRoot + '/home/getTraktToken', {
                                "trakt_pin": $('#trakt_pin').val()
                            }).done(function (data) {
                                $('#testTrakt-result').html(data);
                                $('#authTrakt').addClass('d-none');
                                $('#trakt_pin').addClass('d-none');
                                $('#TraktGetPin').addClass('d-none');
                            });
                        }
                    });

                    $('#testTrakt').click(function () {
                        var trakt_username = $.trim($('#trakt_username').val());
                        var trakt_trending_blacklist = $.trim($('#trakt_blacklist_name').val());
                        if (!trakt_username) {
                            $('#testTrakt-result').html(gt('Please fill out the necessary fields above.'));
                            if (!trakt_username) {
                                $('#trakt_username').addClass('warning');
                            } else {
                                $('#trakt_username').removeClass('warning');
                            }
                            return;
                        }

                        if (/\s/g.test(trakt_trending_blacklist)) {
                            $('#testTrakt-result').html(gt('Check blacklist name; the value need to be a trakt slug'));
                            $('#trakt_blacklist_name').addClass('warning');
                            return;
                        }
                        $('#trakt_username').removeClass('warning');
                        $('#trakt_blacklist_name').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testTrakt-result').html(SICKRAGE.loadingHTML);
                        $.get(SICKRAGE.srWebRoot + '/home/testTrakt', {
                            'username': trakt_username,
                            'blacklist_name': trakt_trending_blacklist
                        }).done(function (data) {
                            $('#testTrakt-result').html(data);
                            $('#testTrakt').prop('disabled', false);
                        });
                    });

                    $('#testEmail').click(function () {
                        var status, host, port, tls, from, user, pwd, err, to;
                        status = $('#testEmail-result');
                        status.html(SICKRAGE.loadingHTML);
                        host = $('#email_host').val();
                        host = host.length > 0 ? host : null;
                        port = $('#email_port').val();
                        port = port.length > 0 ? port : null;
                        tls = $('#email_tls').prop('checked');
                        from = $('#email_from').val();
                        from = from.length > 0 ? from : 'root@localhost';
                        user = $('#email_user').val().trim();
                        pwd = $('#email_password').val();
                        err = '';
                        if (host === null) {
                            err += '<li style="color: red;">' + gt('You must specify an SMTP hostname!') + '</li>';
                        }
                        if (port === null) {
                            err += '<li style="color: red;">' + gt('You must specify an SMTP port!') + '</li>';
                        } else if (port.match(/^\d+$/) === null || parseInt(port, 10) > 65535) {
                            err += '<li style="color: red;">' + gt('SMTP port must be between 0 and 65535!') + '</li>';
                        }
                        if (err.length > 0) {
                            err = '<ol>' + err + '</ol>';
                            status.html(err);
                        } else {
                            to = prompt(gt('Enter an email address to send the test to:'), null);
                            if (to === null || to.length === 0 || to.match(/.*@.*/) === null) {
                                status.html('<p style="color: red;">' + gt('You must provide a recipient email address!') + '</p>');
                            } else {
                                $.get(SICKRAGE.srWebRoot + '/home/testEmail', {
                                    host: host,
                                    port: port,
                                    smtp_from: from,
                                    use_tls: tls,
                                    user: user,
                                    pwd: pwd,
                                    to: to
                                }, function (msg) {
                                    $('#testEmail-result').html(msg);
                                });
                            }
                        }
                    });

                    $('#testNMA').click(function () {
                        var nma_api = $.trim($('#nma_api').val());
                        var nma_priority = $('#nma_priority').val();
                        if (!nma_api) {
                            $('#testNMA-result').html(gt('Please fill out the necessary fields above.'));
                            $('#nma_api').addClass('warning');
                            return;
                        }
                        $('#nma_api').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testNMA-result').html(SICKRAGE.loadingHTML);
                        $.get(SICKRAGE.srWebRoot + '/home/testNMA', {
                            'nma_api': nma_api,
                            'nma_priority': nma_priority
                        }).done(function (data) {
                            $('#testNMA-result').html(data);
                            $('#testNMA').prop('disabled', false);
                        });
                    });

                    $('#testPushalot').click(function () {
                        var pushalot_authorizationtoken = $.trim($('#pushalot_authorizationtoken').val());
                        if (!pushalot_authorizationtoken) {
                            $('#testPushalot-result').html(gt('Please fill out the necessary fields above.'));
                            $('#pushalot_authorizationtoken').addClass('warning');
                            return;
                        }
                        $('#pushalot_authorizationtoken').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testPushalot-result').html(SICKRAGE.loadingHTML);
                        $.get(SICKRAGE.srWebRoot + '/home/testPushalot', {'authorizationToken': pushalot_authorizationtoken}).done(function (data) {
                            $('#testPushalot-result').html(data);
                            $('#testPushalot').prop('disabled', false);
                        });
                    });

                    $('#testPushbullet').click(function () {
                        var pushbullet_api = $.trim($('#pushbullet_api').val());
                        if (!pushbullet_api) {
                            $('#testPushbullet-result').html(gt('Please fill out the necessary fields above.'));
                            $('#pushbullet_api').addClass('warning');
                            return;
                        }
                        $('#pushbullet_api').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testPushbullet-result').html(SICKRAGE.loadingHTML);
                        $.get(SICKRAGE.srWebRoot + '/home/testPushbullet', {'api': pushbullet_api}).done(function (data) {
                            $('#testPushbullet-result').html(data);
                            $('#testPushbullet').prop('disabled', false);
                        });
                    });

                    $('#getPushbulletDevices').click(function () {
                        SICKRAGE.config.notifications.get_pushbullet_devices(gt("Device list updated. Please choose a device to push to."));
                    });

                    // we have to call this function on dom ready to create the devices select
                    if ($('#use_pushbullet').prop('checked')) {
                        SICKRAGE.config.notifications.get_pushbullet_devices();
                    }

                    $('#email_show').on('change', function () {
                        var key = parseInt($('#email_show').val(), 10);
                        $.getJSON(SICKRAGE.srWebRoot + "/home/loadShowNotifyLists", function (notifyData) {
                            if (notifyData._size > 0) {
                                $('#email_show_list').val(key >= 0 ? notifyData[key.toString()].list : '');
                            }
                        });
                    });

                    $('#prowl_show').on('change', function () {
                        var key = parseInt($('#prowl_show').val(), 10);
                        $.getJSON(SICKRAGE.srWebRoot + "/home/loadShowNotifyLists", function (notifyData) {
                            if (notifyData._size > 0) {
                                $('#prowl_show_list').val(key >= 0 ? notifyData[key.toString()].prowl_notify_list : '');
                            }
                        });
                    });

                    // Load the per show notify lists everytime this page is loaded
                    SICKRAGE.config.notifications.load_show_notify_lists();

                    $('#email_show_save').click(function () {
                        $.get(SICKRAGE.srWebRoot + "/home/saveShowNotifyList",
                            {
                                'show': $('#email_show').val(),
                                'emails': $('#email_show_list').val()
                            })
                            .done(function () {
                                // Reload the per show notify lists to reflect changes
                                SICKRAGE.config.notifications.load_show_notify_lists();
                            });
                    });

                    // show instructions for plex when enabled
                    $('#use_plex').click(function () {
                        if ($(this).is(':checked')) {
                            $('.plexinfo').removeClass('d-none');
                        } else {
                            $('.plexinfo').addClass('d-none');
                        }
                    });
                },

                get_pushbullet_devices: function (msg) {
                    if (msg) {
                        $('#testPushbullet-result').html(SICKRAGE.loadingHTML);
                    }

                    var pushbullet_api = $("#pushbullet_api").val();

                    if (!pushbullet_api) {
                        $('#testPushbullet-result').html(gt("You didn't supply a Pushbullet api key"));
                        $("#pushbullet_api").focus();
                        return false;
                    }

                    $.get(SICKRAGE.srWebRoot + "/home/getPushbulletDevices", {'api': pushbullet_api}, function (data) {
                        var devices = $.parseJSON(data).devices;
                        var current_pushbullet_device = $("#pushbullet_device").val();
                        $("#pushbullet_device_list").html('');
                        for (var i = 0; i < devices.length; i++) {
                            if (devices[i].active === true) {
                                if (current_pushbullet_device === devices[i].iden) {
                                    $("#pushbullet_device_list").append('<option value="' + devices[i].iden + '" selected>' + devices[i].nickname + '</option>');
                                } else {
                                    $("#pushbullet_device_list").append('<option value="' + devices[i].iden + '">' + devices[i].nickname + '</option>');
                                }
                            }
                        }
                        if (current_pushbullet_device === '') {
                            $("#pushbullet_device_list").prepend('<option value="" selected>All devices</option>');
                        } else {
                            $("#pushbullet_device_list").prepend('<option value="">All devices</option>');
                        }
                        if (msg) {
                            $('#testPushbullet-result').html(msg);
                        }
                    });

                    $("#pushbullet_device_list").change(function () {
                        $("#pushbullet_device").val($("#pushbullet_device_list").val());
                        $('#testPushbullet-result').html(gt('Don\'t forget to save your new pushbullet settings.'));
                    });
                },

                load_show_notify_lists: function () {
                    $.getJSON(SICKRAGE.srWebRoot + "/home/loadShowNotifyLists", function (list) {
                        var html, s;
                        if (list._size === 0) {
                            return;
                        }

                        // Convert the 'list' object to a js array of objects so that we can sort it
                        var _list = [];
                        for (s in list) {
                            if (Object.prototype.hasOwnProperty.call(list, s) && s.charAt(0) !== '_') {
                                _list.push(list[s]);
                            }
                        }
                        var sortedList = _list.sort(function (a, b) {
                            if (a.name < b.name) {
                                return -1;
                            }
                            if (a.name > b.name) {
                                return 1;
                            }
                            return 0;
                        });
                        html = '<option value="-1">-- Select --</option>';
                        for (s in sortedList) {
                            if (Object.prototype.hasOwnProperty.call(sortedList, s) && sortedList[s].id && sortedList[s].name) {
                                html += '<option value="' + sortedList[s].id + '">' + $('<div/>').text(sortedList[s].name).html() + '</option>';
                            }
                        }
                        $('#email_show').html(html);
                        $('#email_show_list').val('');

                        $('#prowl_show').html(html);
                        $('#prowl_show_list').val('');
                    });
                }
            },

            backup_restore: function () {
                $('#Backup').click(function () {
                    $("#Backup").attr("disabled", true);
                    $('#Backup-result').html(SICKRAGE.loadingHTML);
                    var backupDir = $("#backupDir").val();
                    $.get(SICKRAGE.srWebRoot + "/config/backuprestore/backup", {'backupDir': backupDir})
                        .done(function (data) {
                            $('#Backup-result').html(data);
                            $("#Backup").attr("disabled", false);
                        });
                });

                $('#Restore').click(function () {
                    $("#Restore").attr("disabled", true);
                    $('#Restore-result').html(SICKRAGE.loadingHTML);
                    $.get(SICKRAGE.srWebRoot + "/config/backuprestore/restore",
                        {
                            'backupFile': $("#backupFile").val(),
                            'restore_database': $("#restore_database").prop('checked'),
                            'restore_config': $("#restore_config").prop('checked'),
                            'restore_cache': $("#restore_cache").prop('checked')
                        })
                        .done(function (data) {
                            $('#Restore-result').html(data);
                            $("#Restore").attr("disabled", false);
                        });
                });

                $('#backupDir').fileBrowser({
                    title: gt('Select backup folder to save to'),
                    key: 'backupPath'
                });

                $('#backupFile').fileBrowser({
                    title: gt('Select backup files to restore'),
                    key: 'backupFile',
                    includeFiles: 1
                });
            },

            providers: {
                newznabProviders: [],
                torrentRssProviders: [],
                newznabProvidersCapabilities: [],

                init: function () {
                    $(document).on('change', '.newznab_key', function () {
                        var providerId = $(this).attr('id');
                        providerId = providerId.substring(0, providerId.length - '_key'.length);

                        var url = $('#' + providerId + '_url').val();
                        var cat = $('#' + providerId + '_cat').val();
                        var key = $(this).val();

                        SICKRAGE.config.providers.updateNewznabProvider(providerId, url, key, cat);
                    });

                    $('#newznab_key,#newznab_url').change(function () {
                        var selectedProvider = $('#editANewznabProvider :selected').val();

                        if (selectedProvider === "addNewznab") {
                            return;
                        }

                        var url = $('#newznab_url').val();
                        var key = $('#newznab_key').val();

                        var cat = $('#newznab_cat option').map(function (i, opt) {
                            return $(opt).text();
                        }).toArray().join(',');

                        SICKRAGE.config.providers.updateNewznabProvider(selectedProvider, url, key, cat);
                    });

                    $('#torrentrss_url,#torrentrss_cookies,#torrentrss_titleTAG').change(function () {
                        var selectedProvider = $('#editATorrentRssProvider :selected').val();

                        if (selectedProvider === "addTorrentRss") {
                            return;
                        }

                        var url = $('#torrentrss_url').val();
                        var cookies = $('#torrentrss_cookies').val();
                        var titleTAG = $('#torrentrss_titleTAG').val();

                        SICKRAGE.config.providers.updateTorrentRssProvider(selectedProvider, url, cookies, titleTAG);
                    });

                    $(document).on('change', '#editAProvider', function () {
                        SICKRAGE.config.providers.showHideProviders();
                    });

                    $('#editANewznabProvider').change(function () {
                        SICKRAGE.config.providers.populateNewznabSection();
                    });

                    $('#editATorrentRssProvider').change(function () {
                        SICKRAGE.config.providers.populateTorrentRssSection();
                    });

                    $(document).on('click', '.provider_enabler', function () {
                        SICKRAGE.config.providers.refreshProviderList();
                    });

                    $('#newznab_cat_update').click(function () {
                        // Maybe check if there is anything selected?
                        $("#newznab_cat option").each(function () {
                            $(this).remove();
                        });

                        var newOptions = [];

                        // When the update botton is clicked, loop through the capabilities list
                        // and copy the selected category id's to the category list on the right.
                        $("#newznab_cap option:selected").each(function () {
                            var selectedCat = $(this).val();
                            newOptions.push({text: selectedCat, value: selectedCat});
                        });

                        SICKRAGE.config.providers.replaceProviderOptions("#newznab_cat", newOptions);

                        var selectedProvider = $("#editANewznabProvider :selected").val();
                        if (selectedProvider === "addNewznab") {
                            return;
                        }

                        var url = $('#newznab_url').val();
                        var key = $('#newznab_key').val();

                        var cat = $('#newznab_cat option').map(function (i, opt) {
                            return $(opt).text();
                        }).toArray().join(',');

                        $("#newznab_cat option:not([value])").remove();

                        SICKRAGE.config.providers.updateNewznabProvider(selectedProvider, url, key, cat);
                    });


                    $('#newznab_add').click(function () {
                        var name = $.trim($('#newznab_name').val());
                        var url = $.trim($('#newznab_url').val());
                        var key = $.trim($('#newznab_key').val());

                        var cat = $.trim($('#newznab_cat option').map(function (i, opt) {
                            return $(opt).text();
                        }).toArray().join(','));

                        if (!name || !url || !key) {
                            return;
                        }

                        var params = {name: name};

                        // send to the form with ajax, get a return value
                        $.getJSON(SICKRAGE.srWebRoot + '/config/providers/canAddNewznabProvider', params, function (data) {
                            if (data.error !== undefined) {
                                alert(data.error);
                                return;
                            }
                            SICKRAGE.config.providers.addNewznabProvider(data.success, name, url, key, cat, 'false');
                            SICKRAGE.config.providers.refreshEditAProvider();
                        });
                    });

                    $('.newznab_delete').click(function () {
                        var selectedProvider = $('#editANewznabProvider :selected').val();
                        SICKRAGE.config.providers.deleteNewznabProvider(selectedProvider);
                    });

                    $('#torrentrss_add').click(function () {
                        var name = $('#torrentrss_name').val();
                        var url = $('#torrentrss_url').val();
                        var cookies = $('#torrentrss_cookies').val();
                        var titleTAG = $('#torrentrss_titleTAG').val();
                        var params = {name: name, url: url, cookies: cookies, titleTAG: titleTAG};

                        // send to the form with ajax, get a return value
                        $.getJSON(SICKRAGE.srWebRoot + '/config/providers/canAddTorrentRssProvider', params, function (data) {
                            if (data.error !== undefined) {
                                alert(data.error);
                                return;
                            }

                            SICKRAGE.config.providers.addTorrentRssProvider(data.success, name, url, cookies, titleTAG, 'false');
                            SICKRAGE.config.providers.refreshEditAProvider();
                        });
                    });

                    $('.torrentrss_delete').on('click', function () {
                        SICKRAGE.config.providers.deleteTorrentRssProvider($('#editATorrentRssProvider :selected').val());
                        SICKRAGE.config.providers.refreshEditAProvider();
                    });

                    $(document).on('change', "[class='providerDiv_tip'] input", function () {
                        $('div .providerDiv ' + "[name=" + $(this).attr('name') + "]").replaceWith($(this).clone());
                        $('div .providerDiv ' + "[newznab_name=" + $(this).attr('id') + "]").replaceWith($(this).clone());
                    });

                    $(document).on('change', "[class='providerDiv_tip'] select", function () {
                        $(this).find('option').each(function () {
                            if ($(this).is(':selected')) {
                                $(this).prop('defaultSelected', true);
                            } else {
                                $(this).prop('defaultSelected', false);
                            }
                        });
                        $('div .providerDiv ' + "[name=" + $(this).attr('name') + "]").empty().replaceWith($(this).clone());
                    });

                    $(document).on('change', '.seed_option', function () {
                        var providerId = $(this).attr('id').split('_')[0];
                        SICKRAGE.config.providers.makeTorrentOptionString(providerId);
                    });

                    $("#provider_order_list").sortable({
                        placeholder: 'ui-state-highlight',
                        update: function () {
                            SICKRAGE.config.providers.refreshProviderList();
                        }
                    });

                    $("#provider_order_list").disableSelection();

                    if ($('#editANewznabProvider').length) {
                        SICKRAGE.config.providers.populateNewznabSection();
                    }

                    var newznab_providers = SICKRAGE.getMeta('NEWZNAB_PROVIDERS').split('!!!');
                    for (var newznab_id = 0; newznab_id < newznab_providers.length; newznab_id++) {
                        var newznab_provider = newznab_providers[newznab_id];
                        if (newznab_provider.length > 0) {
                            SICKRAGE.config.providers.addNewznabProvider.apply(this, newznab_provider.split('|'));
                        }
                    }

                    var torrentrss_providers = SICKRAGE.getMeta('TORRENTRSS_PROVIDERS').split('!!!');
                    for (var torrentrss_id = 0; torrentrss_id < torrentrss_providers.length; torrentrss_id++) {
                        var torrentrss_provider = torrentrss_providers[torrentrss_id];
                        if (torrentrss_provider.length > 0) {
                            SICKRAGE.config.providers.addTorrentRssProvider.apply(this, torrentrss_provider.split('|'));
                        }
                    }

                    SICKRAGE.config.providers.showHideProviders();
                },

                showHideProviders: function () {
                    $('.providerDiv').each(function () {
                        var providerName = $(this).attr('id');
                        var selectedProvider = $('#editAProvider :selected').val();

                        if (selectedProvider + 'Div' === providerName) {
                            $(this).show();
                        } else {
                            $(this).hide();
                        }
                    });
                },

                findProvider: function (loopThroughArray, searchFor) {
                    var found = false;

                    loopThroughArray.forEach(function (rootObject) {
                        if (rootObject.name === searchFor) {
                            found = true;
                        }
                    });
                    return found;
                },

                getNewznabCategories: function (isDefault, selectedProvider) {

                    var name = selectedProvider[0];
                    var url = selectedProvider[1];
                    var key = selectedProvider[2];

                    if (!name || !url || !key) {
                        return;
                    }

                    var params = {url: url, name: name, key: key};

                    $(".updating_categories").wrapInner('<span>' + SICKRAGE.loadingHTML + ' Updating Categories ...</span>');
                    $.getJSON(SICKRAGE.srWebRoot + '/config/providers/getNewznabCategories', params, function (data) {
                        SICKRAGE.config.providers.updateNewznabCaps(data, selectedProvider);
                    }).always(function () {
                        $(".updating_categories").empty();
                    });
                },

                addNewznabProvider: function (id, name, url, key, cat, isDefault, showProvider) {
                    url = $.trim(url);
                    if (!url) {
                        return;
                    }

                    if (!/^https?:\/\//i.test(url)) {
                        url = "http://" + url;
                    }

                    if (url.match('/$') === null) {
                        url = url + '/';
                    }

                    SICKRAGE.config.providers.newznabProviders[id] = [isDefault, [name, url, key, cat]];

                    if (isDefault !== 'true') {
                        $('#editANewznabProvider').append($("<option></option>").attr("value", id).text(name));
                        SICKRAGE.config.providers.populateNewznabSection();
                    }

                    if ($('#provider_order_list > #' + id).length === 0 && showProvider !== 'false') {
                        $('#provider_order_list').append('<div class="list-group-item list-group-item-action list-group-item-dark rounded mb-1 p-2" id="' + id + '"><div class="align-middle"><label class="form-check-label" for="enable_' + id + '"><input type="checkbox" id="enable_' + id + '" class="provider_enabler text-left" checked><a href="' + SICKRAGE.anonURL + url + '" class="text-right" target="_new"> <i class="sickrage-providers sickrage-providers-newznab"></i></a> <span class="font-weight-bold">' + name + '</span></label><span class="float-right d-inline-block"><i class="fas fa-lock text-danger"></i></span></div>');
                        $('#provider_order_list').sortable("refresh");
                    }

                    SICKRAGE.config.providers.refreshProviderList();
                },

                updateNewznabProvider: function (id, url, key, cat) {
                    SICKRAGE.config.providers.newznabProviders[id][1][1] = url;
                    SICKRAGE.config.providers.newznabProviders[id][1][2] = key;
                    SICKRAGE.config.providers.newznabProviders[id][1][3] = cat;
                    SICKRAGE.config.providers.populateNewznabSection();
                    SICKRAGE.config.providers.refreshProviderList();
                },

                deleteNewznabProvider: function (id) {
                    $("#editANewznabProvider option[value='" + id + "']").remove();
                    $(".list-group #" + id).remove();
                    SICKRAGE.config.providers.populateNewznabSection();
                    delete SICKRAGE.config.providers.newznabProviders[id];
                    SICKRAGE.config.providers.refreshProviderList();
                },

                populateNewznabSection: function () {
                    var selectedProvider = $('#editANewznabProvider :selected').val();
                    var data = '';
                    var isDefault = '';
                    var rrcat = '';

                    if (selectedProvider === 'addNewznab') {
                        data = ['', '', ''];
                        isDefault = 'false';
                        $('#newznab_add_div').show();
                        $('#newznab_update_div').hide();
                        $('#newznab_cat').attr('disabled', 'disabled');
                        $('#newznab_cap').attr('disabled', 'disabled');
                        $('#newznab_cat_update').attr('disabled', 'disabled');
                        $('#newznabcapdiv').hide();

                        $("#newznab_cat option").each(function () {
                            $(this).remove();

                        });

                        $("#newznab_cap option").each(function () {
                            $(this).remove();

                        });

                    } else {
                        data = SICKRAGE.config.providers.newznabProviders[selectedProvider][1];
                        isDefault = SICKRAGE.config.providers.newznabProviders[selectedProvider][0];
                        $('#newznab_add_div').hide();
                        $('#newznab_update_div').show();
                        $('#newznab_cat').removeAttr("disabled");
                        $('#newznab_cap').removeAttr("disabled");
                        $('#newznab_cat_update').removeAttr("disabled");
                        $('#newznabcapdiv').show();
                    }

                    $('#newznab_name').val(data[0]);
                    $('#newznab_url').val(data[1]);
                    $('#newznab_key').val(data[2]);

                    //Check if not already array
                    if (typeof data[3] === 'string') {
                        rrcat = data[3].split(",");
                    } else {
                        rrcat = data[3];
                    }

                    // Update the category select box (on the right)
                    var newCatOptions = [];
                    if (rrcat) {
                        rrcat.forEach(function (cat) {
                            if (cat !== '') {
                                newCatOptions.push({text: cat, value: cat});
                            }
                        });
                        SICKRAGE.config.providers.replaceProviderOptions("#newznab_cat", newCatOptions);
                    }

                    if (selectedProvider === 'addNewznab') {
                        $('#newznab_name').removeAttr("disabled");
                        $('#newznab_url').removeAttr("disabled");
                    } else {
                        $('#newznab_name').attr("disabled", "disabled");

                        if (isDefault === 'true') {
                            $('#newznab_url').attr("disabled", "disabled");
                            $('#newznab_delete').attr("disabled", "disabled");
                        } else {
                            $('#newznab_url').removeAttr("disabled");
                            $('#newznab_delete').removeAttr("disabled");

                            //Get Categories Capabilities
                            if (data[0] && data[1] && data[2] && !SICKRAGE.config.providers.findProvider(SICKRAGE.config.providers.newznabProvidersCapabilities, data[0])) {
                                SICKRAGE.config.providers.getNewznabCategories(isDefault, data);
                            }
                            SICKRAGE.config.providers.updateNewznabCaps(null, data);
                        }
                    }
                },

                updateNewznabCaps: function (newzNabCaps, selectedProvider) {
                    if (newzNabCaps && !SICKRAGE.config.providers.findProvider(SICKRAGE.config.providers.newznabProvidersCapabilities, selectedProvider[0])) {
                        SICKRAGE.config.providers.newznabProvidersCapabilities.push({
                            'name': selectedProvider[0],
                            'categories': newzNabCaps.tv_categories
                        });
                    }

                    //Loop through the array and if currently selected newznab provider name matches one in the array, use it to
                    //update the capabilities select box (on the left).
                    if (selectedProvider[0]) {
                        SICKRAGE.config.providers.newznabProvidersCapabilities.forEach(function (newzNabCap) {
                            if (newzNabCap.name && newzNabCap.name === selectedProvider[0] && newzNabCap.categories instanceof Array) {
                                var newCapOptions = [];
                                newzNabCap.categories.forEach(function (categorySet) {
                                    if (categorySet.id && categorySet.name) {
                                        newCapOptions.push({
                                            value: categorySet.id,
                                            text: categorySet.name + "(" + categorySet.id + ")"
                                        });
                                    }
                                });
                                SICKRAGE.config.providers.replaceProviderOptions("#newznab_cap", newCapOptions);
                            }
                        });
                    }
                },

                addTorrentRssProvider: function (id, name, url, cookies, titleTAG, isDefault, showProvider) {
                    SICKRAGE.config.providers.torrentRssProviders[id] = [name, url, cookies, titleTAG];

                    if (isDefault !== 'true') {
                        $('#editATorrentRssProvider').append($("<option></option>").attr("value", id).text(name));
                        SICKRAGE.config.providers.populateTorrentRssSection();
                    }

                    if ($('#provider_order_list > #' + id).length === 0 && showProvider !== 'false') {
                        $('#provider_order_list').append('<div class="list-group-item list-group-item-action list-group-item-secondary rounded mb-1 p-2" id="' + id + '"><div class="align-middle"><label class="form-check-label" for="enable_' + id + '"><input type="checkbox" id="enable_' + id + '" class="provider_enabler text-left" checked><a href="' + SICKRAGE.anonURL + url + '" class="text-right" target="_new"> <i class="sickrage-providers sickrage-providers-torrentrss"></i></a> <span class="font-weight-bold">' + name + '</span></label><span class="float-right d-inline-block"><i class="fas fa-lock text-danger"></i></span></div>');
                        $('#provider_order_list').sortable("refresh");
                    }

                    SICKRAGE.config.providers.refreshProviderList();
                },

                updateTorrentRssProvider: function (id, url, cookies, titleTAG) {
                    SICKRAGE.config.providers.torrentRssProviders[id][1] = url;
                    SICKRAGE.config.providers.torrentRssProviders[id][2] = cookies;
                    SICKRAGE.config.providers.torrentRssProviders[id][3] = titleTAG;
                    SICKRAGE.config.providers.populateTorrentRssSection();
                    SICKRAGE.config.providers.refreshProviderList();
                },

                deleteTorrentRssProvider: function (id) {
                    $("#editATorrentRssProvider option[value='" + id + "']").remove();
                    $(".list-group #" + id).remove();
                    SICKRAGE.config.providers.populateTorrentRssSection();
                    delete SICKRAGE.config.providers.torrentRssProviders[id];
                    SICKRAGE.config.providers.refreshProviderList();
                },

                populateTorrentRssSection: function () {
                    var selectedProvider = $('#editATorrentRssProvider :selected').val();
                    var data = '';

                    if (selectedProvider === 'addTorrentRss') {
                        data = ['', '', '', 'title'];
                        $('#torrentrss_add_div').show();
                        $('#torrentrss_update_div').hide();
                    } else {
                        data = SICKRAGE.config.providers.torrentRssProviders[selectedProvider];
                        $('#torrentrss_add_div').hide();
                        $('#torrentrss_update_div').show();
                    }

                    $('#torrentrss_name').val(data[0]);
                    $('#torrentrss_url').val(data[1]);
                    $('#torrentrss_cookies').val(data[2]);
                    $('#torrentrss_titleTAG').val(data[3]);

                    if (selectedProvider === 'addTorrentRss') {
                        $('#torrentrss_name').removeAttr("disabled");
                        $('#torrentrss_url').removeAttr("disabled");
                        $('#torrentrss_cookies').removeAttr("disabled");
                        $('#torrentrss_titleTAG').removeAttr("disabled");
                    } else {
                        $('#torrentrss_name').attr("disabled", "disabled");
                        $('#torrentrss_url').removeAttr("disabled");
                        $('#torrentrss_cookies').removeAttr("disabled");
                        $('#torrentrss_titleTAG').removeAttr("disabled");
                        $('#torrentrss_delete').removeAttr("disabled");
                    }
                },

                makeTorrentOptionString: function (providerId) {
                    var seedRatio = $('.providerDiv_tip #' + providerId + '_seed_ratio').prop('value');
                    var seedTime = $('.providerDiv_tip #' + providerId + '_seed_time').prop('value');
                    var processMet = $('.providerDiv_tip #' + providerId + '_process_method').prop('value');
                    var optionString = $('.providerDiv_tip #' + providerId + '_option_string');

                    optionString.val([seedRatio, seedTime, processMet].join('|'));
                },

                refreshProviderList: function () {
                    var idArr = $("#provider_order_list").sortable('toArray');
                    var finalArr = [];
                    var provStrings = [];

                    $.each(idArr, function (key, val) {
                        var checked = +$('#enable_' + val).prop('checked') ? '1' : '0';
                        finalArr.push(val + ':' + checked);
                    });

                    for (var newznab_id in SICKRAGE.config.providers.newznabProviders) {
                        if (Object.prototype.hasOwnProperty.call(SICKRAGE.config.providers.newznabProviders, newznab_id)) {
                            provStrings.push(
                                "newznab|" + SICKRAGE.config.providers.newznabProviders[newznab_id][1].join('|')
                            );
                        }
                    }

                    for (var torrentrss_id in SICKRAGE.config.providers.torrentRssProviders) {
                        if (Object.prototype.hasOwnProperty.call(SICKRAGE.config.providers.torrentRssProviders, torrentrss_id)) {
                            provStrings.push(
                                "torrentrss|" + SICKRAGE.config.providers.torrentRssProviders[torrentrss_id].join('|')
                            );
                        }
                    }

                    $("#provider_strings").val(provStrings.join('!!!'));
                    $("#provider_order").val(finalArr.join('!!!'));

                    SICKRAGE.config.providers.refreshEditAProvider();
                },

                refreshEditAProvider: function () {
                    $('#editAProvider').empty();

                    var idArr = $("#provider_order_list").sortable('toArray');
                    var finalArr = [];
                    $.each(idArr, function (key, val) {
                        if ($('#enable_' + val).prop('checked')) {
                            finalArr.push(val);
                        }
                    });

                    if (finalArr.length > 0) {
                        $('<select>').prop('id', 'editAProvider').addClass('form-control input-sm').appendTo('#provider-list');
                        for (var i = 0; i < finalArr.length; i++) {
                            var provider = finalArr[i];
                            $('#editAProvider').append($('<option>').prop('value', provider).text($.trim($('#' + provider).text()).replace(/\s\*$/, '').replace(/\s\*\*$/, '')));
                        }
                    } else {
                        document.getElementsByClassName('component-desc')[0].innerHTML = gt("No providers available to configure.");
                    }

                    SICKRAGE.config.providers.showHideProviders();
                },

                replaceProviderOptions: function (field, options) {
                    $(field).empty();
                    $.each(options, function (index, option) {
                        $(field).append($("<option></option>").attr("value", option.value).text(option.text));
                    });
                }
            }
        },

        manage: {
            init: function () {
                $.backstretch(SICKRAGE.srWebRoot + '/images/backdrops/manage.jpg');
                $('.backstretch').css("opacity", SICKRAGE.getMeta('sickrage.FANART_BACKGROUND_OPACITY')).fadeIn("500");
            },

            episode_statuses: function () {
                function makeRow(indexerId, season, episode, name, checked) {
                    var row = '';
                    row += ' <tr class="text-dark ' + $('#row_class').val() + ' show-' + indexerId + '">';
                    row += '  <td align="center"><input type="checkbox" class="' + indexerId + '-epcheck" name="toChange" value="' + indexerId + '-' + season + 'x' + episode + '"' + (checked ? ' checked' : '') + '></td>';
                    row += '  <td>' + season + 'x' + episode + '</td>';
                    row += '  <td style="width: 100%">' + name + '</td>';
                    row += ' </tr>';

                    return row;
                }

                $('.allCheck').click(function () {
                    var indexerId = $(this).attr('id').split('-')[1];
                    $('.' + indexerId + '-epcheck').prop('checked', $(this).prop('checked'));
                });

                $('.get_more_eps').click(function () {
                    var curIndexerId = $(this).attr('id');
                    var checked = $('#allCheck-' + curIndexerId).prop('checked');
                    var lastRow = $('tr#' + curIndexerId);
                    var clicked = $(this).attr('data-clicked');
                    var action = $(this).attr('value');

                    if (!clicked) {
                        $.getJSON(SICKRAGE.srWebRoot + '/manage/showEpisodeStatuses', {
                            indexer_id: curIndexerId,
                            whichStatus: $('#oldStatus').val()
                        }, function (data) {
                            $.each(data, function (season, eps) {
                                $.each(eps, function (episode, name) {
                                    //alert(season+'x'+episode+': '+name);
                                    lastRow.after(makeRow(curIndexerId, season, episode, name, checked));
                                });
                            });
                        });
                        $(this).attr('data-clicked', 1);
                        $(this).prop('value', 'Collapse');
                    } else {
                        if (action.toLowerCase() === 'collapse') {
                            $('table tr').filter('.show-' + curIndexerId).hide();
                            $(this).prop('value', 'Expand');
                        } else if (action.toLowerCase() === 'expand') {
                            $('table tr').filter('.show-' + curIndexerId).show();
                            $(this).prop('value', 'Collapse');
                        }
                    }
                });

                // selects all visible episode checkboxes.
                $('.selectAllShows').click(function () {
                    $('.allCheck').each(function () {
                        $(this).prop("checked", true);
                    });
                    $('input[class*="-epcheck"]').each(function () {
                        $(this).prop("checked", true);
                    });
                });

                // clears all visible episode checkboxes and the season selectors
                $('.unselectAllShows').click(function () {
                    $('.allCheck').each(function () {
                        $(this).prop("checked", false);
                    });
                    $('input[class*="-epcheck"]').each(function () {
                        $(this).prop("checked", false);
                    });
                });
            },

            mass_update: function () {
                $("#massUpdateTable:has(tbody tr)").tablesorter({
                    theme: 'bootstrap',
                    sortList: [[1, 0]],
                    textExtraction: {
                        3: function (node) {
                            return $(node).find("span").text().toLowerCase();
                        },
                        4: function (node) {
                            return $(node).find("span").text().toLowerCase();
                        },
                        5: function (node) {
                            return $(node).find("span").text().toLowerCase();
                        },
                        6: function (node) {
                            return $(node).find("span").text().toLowerCase();
                        },
                        7: function (node) {
                            return $(node).find("span").text().toLowerCase();
                        },
                        8: function (node) {
                            return $(node).find("span").text().toLowerCase();
                        },
                        9: function (node) {
                            return $(node).find("span").text().toLowerCase();
                        },
                        10: function (node) {
                            return $(node).find("span").text().toLowerCase();
                        }
                    },
                    headers: {
                        0: {sorter: false},
                        1: {sorter: 'showNames'},
                        2: {sorter: 'showDirs'},
                        3: {sorter: 'quality'},
                        4: {sorter: 'sports'},
                        5: {sorter: 'scene'},
                        6: {sorter: 'anime'},
                        7: {sorter: 'flatten_folders'},
                        8: {sorter: 'skip_downloaded'},
                        9: {sorter: 'paused'},
                        10: {sorter: 'subtitle'},
                        11: {sorter: 'default_ep_status'},
                        12: {sorter: 'status'}
                    }
                });

                $('#submitMassEdit').on('click', function () {
                    var checkArr = [];

                    $('.showCheck:checked').each(function () {
                        checkArr.push($(this).attr('id'));
                    });

                    if (checkArr.length === 0) {
                        return;
                    }

                    window.location = SICKRAGE.srWebRoot + "/manage/massEdit?toEdit=" + checkArr.join('|');
                });

                $('#submitMassUpdate').on('click', function () {
                    var checkArr = [];

                    $('.showCheck:checked').each(function () {
                        checkArr.push($(this).attr('id'));
                    });

                    if (checkArr.length === 0) {
                        return;
                    }

                    $.post(SICKRAGE.srWebRoot + "/manage/massUpdate", {
                        toUpdate: checkArr.join('|')
                    });
                });

                $('#submitMassRescan').on('click', function () {
                    var checkArr = [];

                    $('.showCheck:checked').each(function () {
                        checkArr.push($(this).attr('id'));
                    });

                    if (checkArr.length === 0) {
                        return;
                    }

                    $.post(SICKRAGE.srWebRoot + "/manage/massUpdate", {
                        toRefresh: checkArr.join('|')
                    });
                });

                $('#submitMassRename').on('click', function () {
                    var checkArr = [];

                    $('.showCheck:checked').each(function () {
                        checkArr.push($(this).attr('id'));
                    });

                    if (checkArr.length === 0) {
                        return;
                    }

                    $.post(SICKRAGE.srWebRoot + "/manage/massUpdate", {
                        toRename: checkArr.join('|')
                    });
                });

                $('#submitMassDelete').on('click', function () {
                    var checkArr = [];

                    $('.showCheck:checked').each(function () {
                        checkArr.push($(this).attr('id'));
                    });

                    if (checkArr.length === 0) {
                        return;
                    }

                    $.confirm({
                        theme: 'dark',
                        title: gt("Mass Delete"),
                        content: gt("You have selected to delete " + checkArr.length + " show(s).  Are you sure you wish to continue? All files will be removed from your system."),
                        buttons: {
                            confirm: function () {
                                $.post(SICKRAGE.srWebRoot + "/manage/massUpdate", {
                                    toDelete: checkArr.join('|')
                                });
                            },
                            cancel: {
                                action: function () {
                                }
                            }
                        }
                    });

                });

                $('#submitMassRemove').on('click', function () {
                    var checkArr = [];

                    $('.showCheck:checked').each(function () {
                        checkArr.push($(this).attr('id'));
                    });

                    if (checkArr.length === 0) {
                        return;
                    }

                    $.post(SICKRAGE.srWebRoot + "/manage/massUpdate", {
                        toRemove: checkArr.join('|')
                    });
                });

                $('#submitMassSubtitle').on('click', function () {
                    var checkArr = [];

                    $('.showCheck:checked').each(function () {
                        checkArr.push($(this).attr('id'));
                    });

                    if (checkArr.length === 0) {
                        return;
                    }

                    $.post(SICKRAGE.srWebRoot + "/manage/massUpdate", {
                        toSubtitle: checkArr.join('|')
                    });
                });

                $('.bulkCheck').on('click', function () {
                    $('.showCheck:visible').each(function () {
                        if (!$(this).disabled) {
                            $(this).prop("checked", !this.checked);
                        }
                    });
                });

                // show/hide different types of rows when the checkboxes are changed
                $("#checkboxControls input").change(function () {
                    var whichClass = $(this).attr('id');
                    var status = $('#checkboxControls > input, #' + whichClass).prop('checked');
                    SICKRAGE.showHideRows(whichClass, status);
                });

                // initially show/hide all the rows according to the checkboxes
                $("#checkboxControls input").each(function () {
                    var status = $(this).prop('checked');
                    $("tr." + $(this).attr('id')).each(function () {
                        if (status) {
                            $(this).show();
                        } else {
                            $(this).hide();
                        }
                    });
                });
            },

            mass_edit: {
                init: function () {
                    $('.new_root_dir').change(function () {
                        var curIndex = SICKRAGE.manage.mass_edit.findDirIndex($(this).attr('id'));
                        $('#display_new_root_dir_' + curIndex).html('<b>' + $(this).val() + '</b>');
                    });

                    $('.edit_root_dir').click(function () {
                        var curIndex = SICKRAGE.manage.mass_edit.findDirIndex($(this).attr('id'));
                        var initialDir = $("#new_root_dir_" + curIndex).val();
                        $(this).nFileBrowser(SICKRAGE.manage.mass_edit.editRootDir, {
                            initialDir: initialDir,
                            whichId: curIndex
                        });
                    });

                    $('.delete_root_dir').click(function () {
                        var curIndex = SICKRAGE.manage.mass_edit.findDirIndex($(this).attr('id'));
                        $('#new_root_dir_' + curIndex).val(null);
                        $('#display_new_root_dir_' + curIndex).html('<b>' + gt('DELETED') + '</b>');
                    });
                },

                findDirIndex: function (which) {
                    var dirParts = which.split('_');
                    return dirParts[dirParts.length - 1];
                },

                editRootDir: function (path, options) {
                    $('#new_root_dir_' + options.whichId).val(path);
                    $('#new_root_dir_' + options.whichId).change();
                }
            },

            backlog_overview: function () {
                $('#pickShow').change(function () {
                    var id = $(this).val();
                    if (id) {
                        $('html,body').animate({scrollTop: $('#show-' + id).offset().top - 25}, 'slow');
                    }
                });
            },

            failed_downloads: function () {
                $("#failedTable:has(tbody tr)").tablesorter({
                    theme: 'bootstrap',
                    sortList: [[0, 0]],
                    headers: {3: {sorter: false}}
                });

                $('#limit').change(function (event) {
                    window.location.href = SICKRAGE.srWebRoot + '/manage/failedDownloads/?limit=' + $(event.currentTarget).val();
                });

                $('#submitMassRemove').on('click', function () {
                    const removeArr = [];

                    $('.removeCheck').each(function () {
                        if (this.checked === true) {
                            removeArr.push($(this).attr('id').split('-')[1]);
                        }
                    });

                    if (removeArr.length === 0) {
                        return false;
                    }

                    $.post(SICKRAGE.srWebRoot + '/manage/failedDownloads', 'toRemove=' + removeArr.join('|'), function () {
                        location.reload(true);
                    });
                });

                $('.bulkCheck').on('click', function () {
                    var bulkCheck = this;
                    var whichBulkCheck = $(bulkCheck).attr('id');

                    $('.' + whichBulkCheck + ':visible').each(function () {
                        $(this).prop("checked", bulkCheck.checked);
                    });
                });

                // if ($('.removeCheck').length) {
                //     $('.removeCheck').each(function (name) {
                //         let lastCheck = null;
                //         $(name).on('click', function (event) {
                //             if (!lastCheck || !event.shiftKey) {
                //                 lastCheck = this;
                //                 return;
                //             }
                //
                //             const check = this;
                //             let found = 0;
                //
                //             $(name + ':visible').each(function () {
                //                 if (found === 2) {
                //                     return false;
                //                 }
                //                 if (found === 1) {
                //                     this.checked = lastCheck.checked;
                //                 }
                //                 if (this === check || this === lastCheck) {
                //                     found++;
                //                 }
                //             });
                //         });
                //     });
                // }
            },

            subtitles_missed: function () {
                function makeRow(indexerId, season, episode, name, subtitles, checked) {
                    checked = checked ? ' checked' : '';

                    var row = '';
                    row += ' <tr class="good show-' + indexerId + '">';
                    row += '  <td align="center"><input type="checkbox" class="' + indexerId + '-epcheck" name="toDownload" value="' + indexerId + '-' + season + 'x' + episode + '"' + checked + '></td>';
                    row += '  <td style="width: 1%;">' + season + 'x' + episode + '</td>';
                    row += '  <td>' + name + '</td>';
                    row += ' </tr>';

                    return row;
                }

                $('.allCheck').click(function () {
                    var indexerId = $(this).attr('id').split('-')[1];
                    $('.' + indexerId + '-epcheck').prop('checked', $(this).prop('checked'));
                });

                $('.get_more_eps').click(function () {
                    var indexerId = $(this).attr('id');
                    var checked = $('#allCheck-' + indexerId).prop('checked');
                    var lastRow = $('tr#' + indexerId);
                    var clicked = $(this).attr('data-clicked');
                    var action = $(this).attr('value');

                    if (!clicked) {
                        $.getJSON(SICKRAGE.srWebRoot + '/manage/showSubtitleMissed', {
                            indexer_id: indexerId,
                            whichSubs: $('#selectSubLang').val()
                        }, function (data) {
                            $.each(data, function (season, eps) {
                                $.each(eps, function (episode, data) {
                                    //alert(season+'x'+episode+': '+name);
                                    lastRow.after(makeRow(indexerId, season, episode, data.name, data.subtitles, checked));
                                });
                            });
                        });
                        $(this).attr('data-clicked', 1);
                        $(this).prop('value', 'Collapse');
                    } else {
                        if (action === 'Collapse') {
                            $('table tr').filter('.show-' + indexerId).hide();
                            $(this).prop('value', 'Expand');
                        } else if (action === 'Expand') {
                            $('table tr').filter('.show-' + indexerId).show();
                            $(this).prop('value', 'Collapse');
                        }
                    }
                });

                // selects all visible episode checkboxes.
                $('.selectAllShows').click(function () {
                    $('.allCheck').each(function () {
                        $(this).prop("checked", true);
                    });
                    $('input[class*="-epcheck"]').each(function () {
                        $(this).prop("checked", true);
                    });
                });

                // clears all visible episode checkboxes and the season selectors
                $('.unselectAllShows').click(function () {
                    $('.allCheck').each(function () {
                        $(this).prop("checked", false);
                    });
                    $('input[class*="-epcheck"]').each(function () {
                        $(this).prop("checked", false);
                    });
                });
            }
        },

        logs: {
            init: function () {
            },

            view: function () {
                $('#minLevel,#logFilter,#logSearch').on('change keyup', _.debounce(function () {
                    if ($('#logSearch').val().length > 0) {
                        $('#logFilter option[value="<NONE>"]').prop('selected', true);
                        $('#minLevel option[value=5]').prop('selected', true);
                    }
                    $('#minLevel').prop('disabled', true);
                    $('#logFilter').prop('disabled', true);
                    document.body.style.cursor = 'wait';
                    var url = SICKRAGE.srWebRoot + '/logs/view/?minLevel=' + $('select[name=minLevel]').val() + '&logFilter=' + $('select[name=logFilter]').val() + '&logSearch=' + $('#logSearch').val();
                    $.get(url, function (data) {
                        history.pushState('data', '', url);
                        $('#loglines').html($(data).find('#loglines').html());
                        $('#minLevel').prop('disabled', false);
                        $('#logFilter').prop('disabled', false);
                        document.body.style.cursor = 'default';
                    });
                }, 500));

                setInterval(function () {
                    $.getJSON(SICKRAGE.srWebRoot + '/logs/view/?minLevel=' + $('select[name=minLevel]').val() + '&logFilter=' + $('select[name=logFilter]').val() + '&logSearch=' + $('#logSearch').val() + '&toJson=1', function (data) {
                        $('#loglines').html(data['logs']);
                    });

                }, parseInt($('select[name=refreshInterval]').val()) * 1000);
            }
        }
    };

    // SiCKRAGE Core Namespace Router
    ({
        init: function () {
            var body = document.body,
                controller = body.getAttribute("data-controller"),
                action = body.getAttribute("data-action");

            this.exec("common");
            this.exec(controller);
            this.exec(controller, action);

            $('.loading-spinner').hide();
            $('.main-container').removeClass('d-none')
        },

        exec: function (controller, action) {
            action = (action === undefined) ? "init" : action;
            if (controller !== "" && SICKRAGE[controller] && SICKRAGE[controller][action]) {
                ({
                    "object": SICKRAGE[controller][action].init,
                    "function": SICKRAGE[controller][action]
                })[typeof SICKRAGE[controller][action]]();
            }
        }
    }).init();
});
