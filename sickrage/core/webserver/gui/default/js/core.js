jQuery(document).ready(function ($) {
    // SiCKRAGE Core Namespace Object
    var SICKRAGE = {
        check_notifications: function () {
            var message_url = '/ui/get_messages';
            if ('visible' === document.visibilityState) {
                $.getJSON(message_url, function (data) {
                    $.each(data, function (name, data) {
                        SICKRAGE.notify(data.type, data.title, data.message);
                    });
                });
            }
            setTimeout(function () {
                "use strict";
                SICKRAGE.check_notifications();
            }, 3000);
        },

        notify: function (type, title, message) {
            var myDesktop = {'desktop': true, 'icon': 'images/ico/favicon-64.png'};
            var myStack = {'dir1': 'up', 'dir2': 'left', 'firstpos1': 25, 'firstpos2': 25};

            PNotify.desktop.permission();
            new PNotify({
                desktop: myDesktop,
                stack: myStack,
                addclass: "stack-bottomright",
                delay: 5000,
                hide: true,
                history: false,
                shadow: false,
                styling: 'jqueryui',
                width: '340px',
                type: type,
                title: title,
                text: message.replace(/<br[\s\/]*(?:\s[^>]*)?>/ig, "\n")
                    .replace(/<[\/]?b(?:\s[^>]*)?>/ig, '*')
                    .replace(/<i(?:\s[^>]*)?>/ig, '[').replace(/<[\/]i>/ig, ']')
                    .replace(/<(?:[\/]?ul|\/li)(?:\s[^>]*)?>/ig, '').replace(/<li(?:\s[^>]*)?>/ig, "\n" + '* ')
            });
        },

        anon_url: function (url) {
            if (new URI(url).scheme === null) {
                url = 'http://' + url;
            }

            return SICKRAGE.anonURL + url;
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
                console.log(pyVar + ' is empty, did you forget to add this to main.mako?');
                return meta;
            } else {
                meta = (isNaN(meta) ? meta.toLowerCase() : meta.toString());
                return !(meta === 'false' || meta === 'none' || meta === '0');
            }
        },

        common: {
            init: function () {
                SICKRAGE.srPID = SICKRAGE.getMeta('srPID');
                SICKRAGE.srDefaultPage = SICKRAGE.getMeta('srDefaultPage');
                SICKRAGE.themeSpinner = SICKRAGE.getMeta('themeSpinner');
                SICKRAGE.loading = '<img src="/images/loading16' + SICKRAGE.themeSpinner + '.gif" height="16" width="16" />';
                SICKRAGE.anonURL = SICKRAGE.getMeta('anonURL');

                // init scrollUp
                $.scrollUp({
                    animation: 'fade',
                    scrollImg: {
                        active: true,
                        type: 'background',
                        src: 'images/top.png'
                    }
                });

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

                $.confirm.options = {
                    confirmButton: "Yes",
                    cancelButton: "Cancel",
                    dialogClass: "modal-dialog",
                    post: false,
                    confirm: function (e) {
                        location.href = e.context.href;
                    }
                };

                $('a.shutdown').confirm({
                    title: 'Shutdown',
                    text: 'Are you sure you want to shutdown SiCKRAGE ?'
                });

                $('a.restart').confirm({
                    title: 'Restart',
                    text: 'Are you sure you want to restart SiCKRAGE ?'
                });

                $('a.clearhistory').confirm({
                    title: 'Clear History',
                    text: 'Are you sure you want to clear all download history ?'
                });

                $('a.trimhistory').confirm({
                    title: 'Trim History',
                    text: 'Are you sure you want to trim all download history older than 30 days ?'
                });

                $('a.submiterrors').confirm({
                    title: 'Submit Errors',
                    text: 'Are you sure you want to submit these errors ?<br><br><span class="red-text">Make sure SiCKRAGE is updated and trigger<br> this error with debug enabled before submitting</span>'
                });

                $('a.removeshow').confirm({
                    title: 'Remove Show',
                    text: 'Are you sure you want to remove <span class="footerhighlight">' + $('#showtitle').data('showname') + '</span> from the database?<br><br><input type="checkbox" id="deleteFiles"> <span class="red-text">Check to delete files as well. IRREVERSIBLE</span></input>',
                    confirm: function (e) {
                        location.href = e.context.href + ($('#deleteFiles')[0].checked ? '&full=1' : '');
                    }
                });

                // plot tooltips
                $('.plotInfo').qtip({
                    content: {
                        attr: 'data-tooltip'
                    },
                    position: {
                        viewport: $(window),
                        my: 'left center',
                        adjust: {
                            y: -10,
                            x: 2
                        }
                    },
                    style: {
                        tip: {
                            corner: true,
                            method: 'polygon'
                        },
                        classes: 'qtip-rounded qtip-shadow ui-tooltip-sb'
                    }
                });

                // scene exception tooltips
                $('.title a').qtip({
                    content: {
                        attr: 'data-tooltip'
                    },
                    show: {
                        solo: true
                    },
                    position: {
                        viewport: $(window),
                        my: 'bottom center',
                        at: 'top center',
                        adjust: {
                            y: 10,
                            x: 0
                        }
                    },
                    style: {
                        tip: {
                            corner: true,
                            method: 'polygon'
                        },
                        classes: 'qtip-rounded qtip-shadow ui-tooltip-sb'
                    }
                });

                // rating tooltips
                $('.imdbstars').qtip({
                    content: {
                        attr: 'data-tooltip'
                    },
                    show: {
                        solo: true
                    },
                    position: {
                        viewport: $(window),
                        my: 'right center',
                        at: 'center left',
                        adjust: {
                            y: 0,
                            x: -6
                        }
                    },
                    style: {
                        tip: {
                            corner: true,
                            method: 'polygon'
                        },
                        classes: 'qtip-rounded qtip-shadow ui-tooltip-sb'
                    }
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

                $("#ui-components").tabs({
                    activate: function (event, ui) {
                        var lastOpenedPanel = $(this).data("lastOpenedPanel");
                        //var selected = this.tabs('option', 'selected');

                        if (!lastOpenedPanel) {
                            lastOpenedPanel = $(ui.oldPanel);
                        }

                        if (!$(this).data("topPositionTab")) {
                            $(this).data("topPositionTab", $(ui.newPanel).position().top);
                        }

                        //Dont use the builtin fx effects. This will fade in/out both tabs, we dont want that
                        //Fadein the new tab yourself
                        $(ui.newPanel).hide().fadeIn(0);

                        if (lastOpenedPanel) {
                            // 1. Show the previous opened tab by removing the jQuery UI class
                            // 2. Make the tab temporary position:absolute so the two tabs will overlap
                            // 3. Set topposition so they will overlap if you go from tab 1 to tab 0
                            // 4. Remove position:absolute after animation
                            lastOpenedPanel
                                .toggleClass("ui-tabs-hide")
                                .css("position", "absolute")
                                .css("top", $(this).data("topPositionTab") + "px")
                                .fadeOut(0, function () {
                                    $(this)
                                        .css("position", "");
                                });
                        }

                        //Saving the last tab has been opened
                        $(this).data("lastOpenedPanel", $(ui.newPanel));
                    }
                });

                SICKRAGE.browser.init();
                SICKRAGE.root_dirs.init();
                SICKRAGE.quality_chooser.init();

                SICKRAGE.check_notifications();
            }
        },

        ajax_search: {
            searchStatusUrl: '/home/getManualSearchStatus',
            failedDownload: false,
            qualityDownload: false,
            selectedEpisode: '',
            manualSearches: [],

            init: function () {
                PNotify.prototype.options.maxonscreen = 5;

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
                    var loadingImage = 'loading16.gif';
                    var queuedImage = 'queued.png';
                    var searchImage = 'search16.png';
                    var htmlContent = '';
                    var el = $('a[id=' + ep.show + 'x' + ep.season + 'x' + ep.episode + ']');
                    var img = el.children('img');
                    var parent = el.parent();

                    if (el) {
                        var rSearchTerm = '';
                        if (ep.searchstatus.toLowerCase() === 'searching') {
                            //el=$('td#' + ep.season + 'x' + ep.episode + '.search img');
                            img.prop('title', 'Searching');
                            img.prop('alt', 'Searching');
                            img.prop('src', '/images/' + loadingImage);
                            SICKRAGE.ajax_search.disableLink(el);
                            // Update Status and Quality
                            //rSearchTerm = /(\w+)\s\((.+?)\)/;
                            htmlContent = ep.searchstatus;

                        } else if (ep.searchstatus.toLowerCase() === 'queued') {
                            //el=$('td#' + ep.season + 'x' + ep.episode + '.search img');
                            img.prop('title', 'Queued');
                            img.prop('alt', 'queued');
                            img.prop('src', '/images/' + queuedImage);
                            SICKRAGE.ajax_search.disableLink(el);
                            htmlContent = ep.searchstatus;
                        } else if (ep.searchstatus.toLowerCase() === 'finished') {
                            //el=$('td#' + ep.season + 'x' + ep.episode + '.search img');
                            img.prop('title', 'Searching');
                            img.prop('alt', 'searching');
                            img.parent().prop('class', 'epRetry');
                            img.prop('src', '/images/' + searchImage);
                            SICKRAGE.ajax_search.enableLink(el);

                            // Update Status and Quality
                            rSearchTerm = /(\w+)\s\((.+?)\)/;
                            htmlContent = ep.status.replace(rSearchTerm, "$1" + ' <span class="quality ' + ep.quality + '">' + "$2" + '</span>');
                            parent.closest('tr').prop("class", ep.overview + " season-" + ep.season + " seasonstyle");
                        }
                        // update the status column if it exists
                        parent.siblings('.col-status').html(htmlContent);

                    }
                    var elementCompleteEpisodes = $('a[id=forceUpdate-' + ep.show + 'x' + ep.season + 'x' + ep.episode + ']');
                    var imageCompleteEpisodes = elementCompleteEpisodes.children('img');
                    if (elementCompleteEpisodes) {
                        if (ep.searchstatus.toLowerCase() === 'searching') {
                            imageCompleteEpisodes.prop('title', 'Searching');
                            imageCompleteEpisodes.prop('alt', 'Searching');
                            imageCompleteEpisodes.prop('src', '/images/' + loadingImage);
                            SICKRAGE.ajax_search.disableLink(elementCompleteEpisodes);
                        } else if (ep.searchstatus.toLowerCase() === 'queued') {
                            imageCompleteEpisodes.prop('title', 'Queued');
                            imageCompleteEpisodes.prop('alt', 'queued');
                            imageCompleteEpisodes.prop('src', '/images/' + queuedImage);
                        } else if (ep.searchstatus.toLowerCase() === 'finished') {
                            imageCompleteEpisodes.prop('title', 'Manual Search');
                            imageCompleteEpisodes.prop('alt', '[search]');
                            imageCompleteEpisodes.prop('src', '/images/' + searchImage);
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
                var img = SICKRAGE.ajax_search.selectedEpisode.children('img');
                img.prop('title', 'loading');
                img.prop('alt', '');
                img.prop('src', '/images/' + options.loadingImage);

                var url = SICKRAGE.ajax_search.selectedEpisode.prop('href');

                if (SICKRAGE.ajax_search.failedDownload === false) {
                    url = url.replace("retryEpisode", "searchEpisode");
                }

                url = url + "&downCurQuality=" + (SICKRAGE.ajax_search.qualityDownload ? '1' : '0');

                $.getJSON(url, function (data) {
                    // if they failed then just put the red X
                    if (data.result.toLowerCase() === 'failure') {
                        imageName = options.noImage;
                        imageResult = 'failed';

                        // if the snatch was successful then apply the corresponding class and fill in the row appropriately
                    } else {
                        imageName = options.loadingImage;
                        imageResult = 'success';
                        // color the row
                        if (options.colorRow) {
                            parent.parent().removeClass('skipped wanted qual good unaired').addClass('snatched');
                        }
                        // applying the quality class
                        var rSearchTerm = /(\w+)\s\((.+?)\)/;
                        htmlContent = data.result.replace(rSearchTerm, "$1" + ' <span class="quality ' + data.quality + '">' + "$2" + '</span>');
                        // update the status column if it exists
                        parent.siblings('.col-status').html(htmlContent);
                        // Only if the queuing was successful, disable the onClick event of the loading image
                        SICKRAGE.ajax_search.disableLink(link);
                    }

                    // put the corresponding image as the result of queuing of the manual search
                    img.prop('title', imageResult);
                    img.prop('alt', imageResult);
                    img.prop('height', options.size);
                    img.prop('src', "/images/" + imageName);
                });

                // don't follow the link
                return false;
            },

            checkManualSearches: function () {
                var pollInterval = 5000;
                var showId = $('#showID').val();
                var url = showId !== undefined ? SICKRAGE.ajax_search.searchStatusUrl + '?show=' + showId : SICKRAGE.ajax_search.searchStatusUrl;
                $.ajax({
                    url: url,
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
            },

            ajaxEpSearch: function (options) {
                var defaults = {
                    size: 16,
                    colorRow: false,
                    loadingImage: 'loading16.gif',
                    queuedImage: 'queued.png',
                    noImage: 'no16.png',
                    yesImage: 'yes16.png'
                };

                options = $.extend({}, defaults, options);

                $('.epRetry').click(function (event) {
                    event.preventDefault();

                    // Check if we have disabled the click
                    if ($(this).prop('enableClick') === '0') {
                        return false;
                    }

                    SICKRAGE.ajax_search.selectedEpisode = $(this);

                    $("#manualSearchModalFailed").modal('show');
                });

                $('.epSearch').click(function (event) {
                    event.preventDefault();

                    // Check if we have disabled the click
                    if ($(this).prop('enableClick') === '0') {
                        return false;
                    }

                    SICKRAGE.ajax_search.selectedEpisode = $(this);

                    if ($(this).parent().parent().children(".col-status").children(".quality").length) {
                        $("#manualSearchModalQuality").modal('show');
                    } else {
                        SICKRAGE.ajax_search.manualSearch(options);
                    }
                });

                $('#manualSearchModalFailed .btn').click(function () {
                    SICKRAGE.ajax_search.failedDownload = ($(this).text().toLowerCase() === 'yes');
                    $("#manualSearchModalQuality").modal('show');
                });

                $('#manualSearchModalQuality .btn').click(function () {
                    SICKRAGE.ajax_search.qualityDownload = ($(this).text().toLowerCase() === 'yes');
                    SICKRAGE.ajax_search.manualSearch(options);
                });
            },

            ajaxEpSubtitlesSearch: function () {
                $('.epSubtitlesSearch').click(function () {
                    var subtitlesTd = $(this).parent().siblings('.col-subtitles');
                    var subtitlesSearchLink = $(this);
                    // fill with the ajax loading gif
                    subtitlesSearchLink.empty();
                    subtitlesSearchLink.append($("<img/>").attr({
                        "src": "/images/loading16.gif",
                        "alt": "",
                        "title": "loading"
                    }));
                    $.getJSON($(this).attr('href'), function (data) {
                        if (data.result.toLowerCase() !== "failure" && data.result.toLowerCase() !== "no subtitles downloaded") {
                            // clear and update the subtitles column with new informations
                            var subtitles = data.subtitles.split(',');
                            subtitlesTd.empty();
                            $.each(subtitles, function (index, language) {
                                if (language !== "" && language !== "und") {
                                    if (index !== subtitles.length - 1) {
                                        subtitlesTd.append($("<img/>").attr({
                                            "src": "/images/subtitles/flags/" + language + ".png",
                                            "alt": language,
                                            "width": 16,
                                            "height": 11
                                        }));
                                    } else {
                                        subtitlesTd.append($("<img/>").attr({
                                            "src": "/images/subtitles/flags/" + language + ".png",
                                            "alt": language,
                                            "width": 16,
                                            "height": 11
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
                    subtitlesMergeLink.append($("<img/>").attr({
                        "src": "/images/loading16.gif",
                        "alt": "",
                        "title": "loading"
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
                title: 'Choose Directory',
                url: '/browser/',
                autocompleteURL: '/browser/complete',
                includeFiles: 0,
                showBrowseButton: true
            },
            fileBrowserDialog: null,
            currentBrowserPath: null,
            currentRequest: null,

            init: function () {
                $.fn.nFileBrowser = SICKRAGE.browser.nFileBrowser;
                $.fn.fileBrowser = SICKRAGE.browser.fileBrowser;
            },

            browse: function (path, endpoint, includeFiles) {
                if (SICKRAGE.browser.currentBrowserPath === path) {
                    return;
                }

                SICKRAGE.browser.currentBrowserPath = path;
                if (SICKRAGE.browser.currentRequest) {
                    SICKRAGE.browser.currentRequest.abort();
                }

                SICKRAGE.browser.fileBrowserDialog.dialog('option', 'dialogClass', 'browserDialog busy');

                SICKRAGE.browser.currentRequest = $.getJSON(endpoint, {
                    path: path,
                    includeFiles: includeFiles
                }, function (data) {
                    SICKRAGE.browser.fileBrowserDialog.empty();
                    var firstVal = data[0];
                    var i = 0;
                    var list, link = null;
                    data = $.grep(data, function () {
                        return i++ !== 0;
                    });

                    $('<input type="text" class="form-control input-sm">')
                        .val(firstVal.currentPath)
                        .on('keypress', function (e) {
                            if (e.which === 13) {
                                SICKRAGE.browser.browse(e.target.value, endpoint, includeFiles);
                            }
                        })
                        .appendTo(SICKRAGE.browser.fileBrowserDialog)
                        .fileBrowser({showBrowseButton: false})
                        .on('autocompleteselect', function (e, ui) {
                            SICKRAGE.browser.browse(ui.item.value, endpoint, includeFiles);
                        });

                    list = $('<ul>').appendTo(SICKRAGE.browser.fileBrowserDialog);
                    $.each(data, function (i, entry) {
                        link = $('<a href="javascript:void(0)">').on('click', function () {
                            if (entry.isFile) {
                                SICKRAGE.browser.currentBrowserPath = entry.path;
                                $('.browserDialog .ui-button:contains("Ok")').click();
                            } else {
                                SICKRAGE.browser.browse(entry.path, endpoint, includeFiles);
                            }
                        }).text(entry.name);
                        if (entry.isFile) {
                            link.prepend('<span class="ui-icon ui-icon-blank"></span>');
                        } else {
                            link.prepend('<span class="ui-icon ui-icon-folder-collapsed"></span>')
                                .on('mouseenter', function () {
                                    $('span', this).addClass('ui-icon-folder-open');
                                })
                                .on('mouseleave', function () {
                                    $('span', this).removeClass('ui-icon-folder-open');
                                });
                        }
                        link.appendTo(list);
                    });
                    $('a', list).wrap('<li class="ui-state-default ui-corner-all">');
                    SICKRAGE.browser.fileBrowserDialog.dialog('option', 'dialogClass', 'browserDialog');
                });
            },

            nFileBrowser: function (callback, options) {
                options = $.extend({}, SICKRAGE.browser.defaults, options);

                // make a fileBrowserDialog object if one doesn't exist already
                if (!SICKRAGE.browser.fileBrowserDialog) {
                    // set up the jquery dialog
                    SICKRAGE.browser.fileBrowserDialog = $('<div id="fileBrowserDialog" style="display:hidden"></div>').appendTo('body').dialog({
                        dialogClass: 'browserDialog',
                        title: options.title,
                        position: ['center', 40],
                        minWidth: Math.min($(document).width() - 80, 650),
                        height: Math.min($(document).height() - 80, $(window).height() - 80),
                        maxHeight: Math.min($(document).height() - 80, $(window).height() - 80),
                        maxWidth: $(document).width() - 80,
                        modal: true,
                        autoOpen: false
                    });
                }

                SICKRAGE.browser.fileBrowserDialog.dialog('option', 'buttons', [
                    {
                        text: "Ok",
                        "class": "btn",
                        click: function () {
                            // store the browsed path to the associated text field
                            callback(SICKRAGE.browser.currentBrowserPath, options);
                            $(this).dialog("close");
                        }
                    },
                    {
                        text: "Cancel",
                        "class": "btn",
                        click: function () {
                            $(this).dialog("close");
                        }
                    }
                ]);

                // set up the browser and launch the dialog
                var initialDir = '';
                if (options.initialDir) {
                    initialDir = options.initialDir;
                }

                SICKRAGE.browser.browse(initialDir, options.url, options.includeFiles);
                SICKRAGE.browser.fileBrowserDialog.dialog('open');

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
                            $(".ui-autocomplete li.ui-menu-item:odd a").addClass("ui-menu-item-alternate");
                        }
                    })
                        .data("ui-autocomplete")._renderItem = function (ul, item) {
                        //highlight the matched search term from the item -- note that this is global and will match anywhere
                        var result_item = item.label;
                        var x = new RegExp("(?![^&;]+;)(?!<[^<>]*)(" + query + ")(?![^<>]*>)(?![^&;]+;)", "gi");
                        result_item = result_item.replace(x, function (FullMatch) {
                            return '<b>' + FullMatch + '</b>';
                        });
                        return $("<li></li>")
                            .data("ui-autocomplete-item", item)
                            .append("<a class='nowrap'>" + result_item + "</a>")
                            .appendTo(ul);
                    };
                }

                var path, callback, ls = false;

                try {
                    ls = !!(localStorage.getItem);
                } catch (e) {
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
                        $('<input type="button" value="Browse&hellip;" class="btn btn-inline fileBrowser">').on('click', function () {
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
                    $.get('/config/general/saveRootDirs', {rootDirString: $('#rootDirText').val()});
                });

                $('#defaultRootDir').click(function () {
                    if ($("#rootDirs option:selected").length) {
                        SICKRAGE.root_dirs.setDefault($("#rootDirs option:selected").attr('id'));
                    }
                    SICKRAGE.root_dirs.refreshRootDirs();
                    $.get('/config/general/saveRootDirs', {rootDirString: $('#rootDirText').val()});
                });

                $('#rootDirs').click(SICKRAGE.root_dirs.refreshRootDirs);

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
                $.get('/config/general/saveRootDirs', {rootDirString: $('#rootDirText').val()});
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
                $.get('/config/general/saveRootDirs', {rootDirString: $('#rootDirText').val()});
            },

            setDefault: function (which, force) {
                console.log('setting default to ' + which);

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

                var logString = '';
                var dirString = '';
                if ($('#whichDefaultRootDir').val().length >= 4) {
                    dirString = $('#whichDefaultRootDir').val().substr(3);
                }
                $('#rootDirs option').each(function () {
                    logString += $(this).val() + '=' + $(this).text() + '->' + $(this).attr('id') + '\n';
                    if (dirString.length) {
                        dirString += '|' + $(this).val();
                    }
                });
                logString += 'def: ' + $('#whichDefaultRootDir').val();
                console.log(logString);

                $('#rootDirText').val(dirString);
                $('#rootDirText').change();
                console.log('rootDirText: ' + $('#rootDirText').val());
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
                    $('#customQuality').show();
                    return;
                } else {
                    $('#customQuality').hide();
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
                if (SICKRAGE.isMeta('sickrage.COMING_EPS_LAYOUT', ['list'])) {
                    var sortCodes = {'date': 0, 'show': 2, 'network': 5};
                    var sort = SICKRAGE.getMeta('sickrage.COMING_EPS_SORT');
                    var sortList = (sort in sortCodes) ? [[sortCodes[sort], 0]] : [[0, 0]];

                    $('#showListTable:has(tbody tr)').tablesorter({
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

                    SICKRAGE.ajax_search.ajaxEpSearch();
                }

                if (SICKRAGE.isMeta('sickrage.COMING_EPS_LAYOUT', ['banner', 'poster'])) {
                    SICKRAGE.ajax_search.ajaxEpSearch({
                        'size': 16,
                        'loadingImage': 'loading16' + SICKRAGE.themeSpinner + '.gif'
                    });
                    $('.ep_summary').hide();
                    $('.ep_summaryTrigger').click(function () {
                        $.next('.ep_summary').slideToggle('normal', function () {
                            $.prev('.ep_summaryTrigger').attr('src', function (i, src) {
                                return $.next('.ep_summary').is(':visible') ? src.replace('plus', 'minus') : src.replace('minus', 'plus');
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
                $("#historyTable:has(tbody tr)").tablesorter({
                    widgets: ['zebra', 'filter'],
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
                    window.location.href = '/history/?limit=' + $(this).val();
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

                        target.parents('.result-wrapper').removeClass('hidden');
                    });
                });

                // Remove the result of an API call
                $('[data-action=clear-result]').on('click', function () {
                    $($(this).data('target')).html('').parents('.result-wrapper').addClass('hidden');
                });

                // Update the list of episodes
                $('[data-action=update-episodes]').on('change', function () {
                    var command = $(this).data('command');
                    var select = $('[data-command=' + command + '][name=episode]');
                    var season = $(this).val();
                    var show = $('[data-command=' + command + '][name=indexerid]').val();
                    var episodes = select.val();

                    if (select !== undefined) {
                        select.removeClass('hidden');
                        select.find('option:gt(0)').remove();

                        for (var episode in episodes[show][season]) {
                            if (episodes[show][season].hasOwnProperty(episode)) {
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
                    var episodes = select.val();

                    if (select !== undefined) {
                        select.removeClass('hidden');
                        select.find('option:gt(0)').remove();

                        for (var season in episodes[show]) {
                            if (episodes[show].hasOwnProperty(season)) {
                                select.append($('<option>', {
                                    value: season,
                                    label: (season === 0) ? 'Specials' : 'Season ' + season
                                }));
                            }
                        }
                    }
                });

                // Enable command search
                $('#command-search').typeahead({
                    source: SICKRAGE.getMeta('commands')
                });
                $('#command-search').on('change', function () {
                    var command = $(this).typeahead('getActive');

                    if (command) {
                        var commandId = command.replace('.', '-');
                        $('[href=#command-' + commandId + ']').click();
                    }
                });
            },

            status: function () {
                $("#schedulerStatusTable").tablesorter({
                    widgets: ['saveSort', 'zebra']
                });
                $("#queueStatusTable").tablesorter({
                    widgets: ['saveSort', 'zebra'],
                    sortList: [[3, 0], [4, 0], [2, 1]]
                });
            }
        },

        google: {
            init: function () {
            },

            login: function () {
                $.ajax({
                    dataType: "json",
                    url: '/google/get_user_code',
                    type: 'POST',
                    success: function (data) {
                        var loginDialog = '<center><h1>' + data.user_code + '</h1><br/>From any computer, please visit <a href="' + data.verification_url + '" target="_blank">' + data.verification_url + '</a> and enter the code</center>';
                        $('#login-dialog').dialog({
                            modal: true,
                            draggable: false,
                            width: '25%',
                            title: 'Link SiCKRAGE'
                        }).html(loginDialog);
                        SICKRAGE.google.poll_auth(data, new Date().getTime() + new Date(data.user_code_expiry).getTime() * 1000, data.interval);
                    }
                });
            },

            logout: function () {
                $.ajax({
                    url: '/google/logout',
                    success: function () {
                        localStorage.clear();
                        location.reload();
                    }
                });
            },

            poll_auth: function (flow_info, lastPollTime, nextPollDelay) {
                if (new Date().getTime() < lastPollTime) {
                    $.ajax({
                        dataType: 'json',
                        url: '/google/get_credentials',
                        data: {flow_info: JSON.stringify(flow_info)},
                        type: 'POST',
                        success: function (response) {
                            if (response.error) {
                                if (response.error === 'slow_down') {
                                    nextPollDelay += 5;
                                }

                                setTimeout(function () {
                                    SICKRAGE.google.poll_auth(flow_info, lastPollTime, nextPollDelay);
                                }, nextPollDelay * 1000);
                            } else {
                                $('#login-dialog').dialog('close');

                                localStorage.setItem('google_refresh_token', response.refresh_token);
                                localStorage.setItem('google_access_token', response.access_token);
                                localStorage.setItem('google_token_type', response.token_type);

                                location.reload();
                            }
                        }
                    });
                }
            },

            refresh_auth: function () {
                $.ajax({
                    dataType: 'json',
                    url: '/google/refresh_credentials',
                    data: {token: localStorage.getItem('google_refresh_token')},
                    type: 'POST',
                    success: function (response) {
                        localStorage.setItem('google_access_token', response.access_token);
                        localStorage.setItem('google_token_type', response.token_type);
                    },
                    error: function () {
                        SICKRAGE.google.logout();
                    }
                });
            }
        },

        home: {
            init: function () {
                SICKRAGE.home.add_show_options();
                SICKRAGE.root_dirs.init();
            },

            index: function () {
                // Resets the tables sorting, needed as we only use a single call for both tables in tablesorter
                $('.resetsorting').on('click', function () {
                    $('table').trigger('filterReset');
                });

                // This needs to be refined to work a little faster.
                $('.progressbar').each(function () {
                    //var showId = $(this).data('show-id');
                    var percentage = $(this).data('progress-percentage');
                    var classToAdd = percentage === 100 ? 100 : percentage > 80 ? 80 : percentage > 60 ? 60 : percentage > 40 ? 40 : 20;
                    $(this).progressbar({value: percentage});
                    if ($(this).data('progress-text')) {
                        $(this).append('<div class="progressbarText" title="' + $(this).data('progress-tip') + '">' + $(this).data('progress-text') + '</div>');
                    }
                    $(this).find('.ui-progressbar-value').addClass('progress-' + classToAdd);
                });

                $("img#network").on('error', function () {
                    $(this).parent().text($(this).attr('alt'));
                    $(this).remove();
                });

                $("#showListTableShows:has(tbody tr), #showListTableAnime:has(tbody tr)").tablesorter({
                    sortList: [[6, 1], [2, 0]],
                    textExtraction: {
                        0: function (node) {
                            return $(node).find('time').attr('datetime');
                        },
                        1: function (node) {
                            return $(node).find('time').attr('datetime');
                        },
                        3: function (node) {
                            return $(node).find("span").prop("title").toLowerCase();
                        },
                        4: function (node) {
                            return $(node).find("span").text().toLowerCase();
                        },
                        5: function (node) {
                            return $(node).find("span:first").text();
                        },
                        6: function (node) {
                            return $(node).find("img").attr("alt");
                        }
                    },
                    widgets: ['saveSort', 'zebra', 'stickyHeaders', 'filter', 'columnSelector'],
                    headers: (function () {
                        if (SICKRAGE.metaToBool('sickrage.FILTER_ROW')) {
                            return {
                                0: {sorter: 'realISODate'},
                                1: {sorter: 'realISODate'},
                                2: {sorter: 'loadingNames'},
                                4: {sorter: 'quality'},
                                5: {sorter: 'eps'},
                                6: {filter: 'parsed'}
                            };
                        } else {
                            return {
                                0: {sorter: 'realISODate'},
                                1: {sorter: 'realISODate'},
                                2: {sorter: 'loadingNames'},
                                4: {sorter: 'quality'},
                                5: {sorter: 'eps'}
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

                if ($("#showListTableShows").find("tbody").find("tr").size() > 0) {
                    $.tablesorter.filter.bindSearch("#showListTableShows", $('.search'));
                }

                if (SICKRAGE.metaToBool('sickrage.ANIME_SPLIT_HOME')) {
                    if ($("#showListTableAnime").find("tbody").find("tr").size() > 0) {
                        $.tablesorter.filter.bindSearch("#showListTableAnime", $('.search'));
                    }
                }

                var $container = [$('#container'), $('#container-anime')];
                $.each($container, function () {
                    $(this).isotope({
                        itemSelector: '.show',
                        sortBy: SICKRAGE.getMeta('sickrage.POSTER_SORTBY'),
                        sortAscending: SICKRAGE.getMeta('sickrage.POSTER_SORTDIR'),
                        layoutMode: 'masonry',
                        masonry: {
                            columnWidth: 13,
                            isFitWidth: true
                        },
                        getSortData: {
                            name: function (itemElem) {
                                var name = $(itemElem).attr('data-name');
                                return (SICKRAGE.metaToBool('sickrage.SORT_ARTICLE') ? (name || '') : (name || '').replace(/^(The|A|An)\s/i, ''));
                            },
                            network: '[data-network]',
                            date: function (itemElem) {
                                var date = $(itemElem).attr('data-date');
                                return date.length && parseInt(date, 10) || Number.POSITIVE_INFINITY;
                            },
                            progress: function (itemElem) {
                                var progress = $(itemElem).attr('data-progress');
                                return progress.length && parseInt(progress, 10) || Number.NEGATIVE_INFINITY;
                            }
                        }
                    });
                });

                $('#postersort').on('change', function () {
                    var sortValue = $(this).value;
                    $('#container').isotope({sortBy: sortValue});
                    $('#container-anime').isotope({sortBy: sortValue});
                    $.get($(this).options[$(this).selectedIndex].getAttribute('data-sort'));
                });

                $('#postersortdirection').on('change', function () {
                    var sortDirection = $(this).value;
                    sortDirection = sortDirection === 'true';
                    $('#container').isotope({sortAscending: sortDirection});
                    $('#container-anime').isotope({sortAscending: sortDirection});
                    $.get($(this).options[$(this).selectedIndex].getAttribute('data-sort'));
                });

                $('#popover').popover({
                    placement: 'bottom',
                    html: true, // required if content has HTML
                    content: '<div id="popover-target"></div>'
                }).on('shown.bs.popover', function () { // bootstrap popover event triggered when the popover opens
                    // call this function to copy the column selection code into the popover
                    $.tablesorter.columnSelector.attachTo($('#showListTableShows'), '#popover-target');
                    if (SICKRAGE.metaToBool('sickrage.ANIME_SPLIT_HOME')) {
                        $.tablesorter.columnSelector.attachTo($('#showListTableAnime'), '#popover-target');
                    }

                });
            },

            display_show: {
                init: function () {
                    SICKRAGE.home.display_show.imdb_stars();
                    SICKRAGE.ajax_search.init();

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
                        $('#pickShow option:selected').prev('option').prop('selected', 'selected');
                        $("#pickShow").change();
                    });

                    $("#nextShow").on('click', function () {
                        $('#pickShow option:selected').next('option').prop('selected', 'selected');
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

                        window.location.href = '/home/setStatus?show=' + $('#showID').attr('value') + '&eps=' + epArr.join('|') + '&status=' + $('#statusSelect').val();
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

                        window.location.href = '/home/deleteEpisode?show=' + $('#showID').attr('value') + '&eps=' + epArr.join('|');
                    });

                    $('.seasonCheck').on('click', function () {
                        var seasCheck = this;
                        var seasNo = $(seasCheck).attr('id');

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
                        window.location.href = '/home/displayShow?show=' + val;
                    });

                    // show/hide different types of rows when the checkboxes are changed
                    $("#checkboxControls input").change(function () {
                        var whichClass = $(this).attr('id');
                        SICKRAGE.home.display_show.showHideRows(whichClass);
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

                    $('.addQTip').each(function () {
                        $(this).css({'cursor': 'help', 'text-shadow': '0px 0px 0.5px #666'});
                        $(this).qtip({
                            show: {solo: true},
                            position: {viewport: $(window), my: 'left center', adjust: {y: -10, x: 2}},
                            style: {
                                tip: {corner: true, method: 'polygon'},
                                classes: 'qtip-rounded qtip-shadow ui-tooltip-sb'
                            }
                        });
                    });

                    $("#showTable, #animeTable").tablesorter({
                        widgets: ['saveSort', 'stickyHeaders', 'columnSelector'],
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
                    })
                    // bootstrap popover event triggered when the popover opens
                        .on('shown.bs.popover', function () {
                            $.tablesorter.columnSelector.attachTo($("#showTable, #animeTable"), '#popover-target');
                        });
                },

                showHideRows: function (whichClass) {
                    var status = $('#checkboxControls > input, #' + whichClass).prop('checked');
                    $("tr." + whichClass).each(function () {
                        if (status) {
                            $(this).show();
                        } else {
                            $(this).hide();
                        }
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

                    $.getJSON('/home/setSceneNumbering', {
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
                                alert('Update failed.');
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

                    $.getJSON('/home/setSceneNumbering', {
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
                                    alert('Update failed.');
                                }
                            }
                        });
                },

                imdb_stars: function () {
                    return $('.imdbstars').each(function (i, e) {
                        $(e).html($('<span/>').width($(e).text() * 12));
                    });
                }
            },

            edit_show: {
                init: function () {
                    var allExceptions = [];

                    $('#location').fileBrowser({title: 'Select Show Location'});

                    $('#submit').click(function () {
                        var allExceptions = [];

                        $("#exceptions_list option").each(function () {
                            allExceptions.push($(this).val());
                        });

                        $("#exceptions_list").val(allExceptions);

                        if (SICKRAGE.metaToBool('show.is_anime')) {
                            SICKRAGE.generate_bwlist();
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

            add_existing_shows: {
                init: function () {
                    $("#tabs").tabs({
                        collapsible: true,
                        selected: (SICKRAGE.metaToBool('sickrage.SORT_ARTICLE') ? -1 : 0)
                    });

                    $('#tableDiv').on('click', '#checkAll', function () {
                        $('.dirCheck').not(this).prop('checked', this.checked);
                    });

                    $('#submitShowDirs').on('click', function () {
                        var dirArr = [];
                        $('.dirCheck').each(function () {
                            if ($(this).prop('checked')) {
                                var show = $(this).attr('id');
                                var indexer = $(this).closest('tr').find('select').val();
                                dirArr.push(encodeURIComponent(indexer + '|' + show));
                            }
                        });

                        if (dirArr.length === 0) {
                            return false;
                        }

                        var url = '/home/addShows/addExistingShows?promptForSettings=' + ($('#promptForSettings').prop('checked') ? 'on' : 'off') + '&shows_to_add=' + dirArr.join('&shows_to_add=');
                        if (url.length < 2083) {
                            window.location.href = url;
                        } else {
                            alert("You've selected too many shows, please uncheck some and try again. [" + url.length + "/2083 characters]");
                        }
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
                            $('#rootDirStaticList').append('<li class="ui-state-default ui-corner-all"><input type="checkbox" class="cb dir_check" id="' + $(w).val() + '" checked=checked> <label for="' + $(w).val() + '"><b>' + $(w).val() + '</b></label></li>');
                        });
                        SICKRAGE.home.add_existing_shows.loadContent();
                    });

                    $('#rootDirStaticList').on('click', '.dir_check', SICKRAGE.home.add_existing_shows.loadContent);

                    $('#tableDiv').on('click', '.showManage', function (event) {
                        event.preventDefault();
                        $("#tabs").tabs('option', 'active', 0);
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

                    $('#tableDiv').html('<img id="searchingAnim" src="/images/loading32.gif" height="32" width="32" /> loading folders...');
                    $.get('/home/addShows/massAddTable/', url, function (data) {
                        $('#tableDiv').html(data);
                        $("#addRootDirTable").tablesorter({
                            sortList: [[1, 0]],
                            widgets: ['zebra'],
                            headers: {
                                0: {sorter: false}
                            }
                        });
                    });
                }
            },

            postprocess: function () {
                $('#episodeDir').fileBrowser({
                    title: 'Select Unprocessed Episode Folder',
                    key: 'postprocessPath'
                });
            },

            trending_shows: {
                init: function () {
                    // initialise combos for dirty page refreshes
                    $('#showsort').val('original');
                    $('#showsortdirection').val('asc');

                    var $container = [$('#container')];
                    $.each($container, function () {
                        $(this).isotope({
                            itemSelector: '.trakt_show',
                            sortBy: 'original-order',
                            layoutMode: 'fitRows',
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
                                $('#container').isotope({sortBy: 'random'});
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
                        $('#container').isotope({sortBy: sortCriteria});
                    });

                    $('#showsortdirection').on('change', function () {
                        $('#container').isotope({sortAscending: ('asc' === $(this).value)});
                    });

                    $('#trendingShows').loadContent('/home/addShows/getTrendingShows/', 'Loading trending shows...', 'Trakt timed out, refresh page to try again');

                    $('#container').isotope({
                        itemSelector: '.trakt_show',
                        layoutMode: 'fitRows'
                    });
                },

                loadContent: function (path, loadingTxt, errorTxt) {
                    $(this).html('<img id="searchingAnim" src="/images/loading32' + SICKRAGE.themeSpinner + '.gif" height="32" width="32" />&nbsp;' + loadingTxt);
                    $(this).load(path + ' #container', function (response, status) {
                        if (status === "error") {
                            $(this).empty().html(errorTxt);
                        }
                    });
                }
            },

            recommended_shows: {
                init: function () {
                    $("#tabs").tabs({
                        collapsible: true,
                        selected: (SICKRAGE.metaToBool('sickrage.SORT_ARTICLE') ? -1 : 0)
                    });

                    // initialise combos for dirty page refreshes
                    $('#showsort').val('original');
                    $('#showsortdirection').val('asc');

                    var $container = [$('#container')];
                    $.each($container, function () {
                        $(this).isotope({
                            itemSelector: '.trakt_show',
                            sortBy: 'original-order',
                            layoutMode: 'fitRows',
                            getSortData: {
                                name: function (itemElem) {
                                    var name = $(itemElem).attr('data-name');
                                    return (SICKRAGE.metaToBool('sickrage.SORT_ARTICLE') ? (name || '') : (name || '').replace(/^(The|A|An)\s/i, ''));
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
                                $('#container').isotope({sortBy: 'random'});
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
                        $('#container').isotope({sortBy: sortCriteria});
                    });

                    $('#showsortdirection').on('change', function () {
                        $('#container').isotope({sortAscending: ('asc' === $(this).value)});
                    });

                    $('#recommendedShows').loadContent('/home/addShows/getRecommendedShows/', 'Loading recommended shows...', 'Trakt timed out, refresh page to try again');

                    $('#container').isotope({
                        itemSelector: '.trakt_show',
                        layoutMode: 'fitRows'
                    });
                },

                loadContent: function (path, loadingTxt, errorTxt) {
                    $(this).html('<img id="searchingAnim" src="/images/loading32' + SICKRAGE.themeSpinner + '.gif" height="32" width="32" />&nbsp;' + loadingTxt);
                    $(this).load(path + ' #container', function (response, status) {
                        if (status === "error") {
                            $(this).empty().html(errorTxt);
                        }
                    });
                }
            },

            popular_shows: function () {
                $("#popularShows:has(tbody tr)").tablesorter({
                    sortList: [[2, 1]]
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

                    window.location.href = '/home/doRename?show=' + $('#showID').attr('value') + '&eps=' + epArr.join('|');
                });

            },

            restart: function () {
                var checkIsAlive = setInterval(function () {
                    $.ajax({
                        url: '/home/is_alive/',
                        dataType: 'jsonp',
                        jsonp: 'srcallback',
                        success: function (data) {
                            // if this is before we've even shut down then just try again later
                            if (SICKRAGE.srPID === '' || data.msg === SICKRAGE.srPID) {
                                $('#shut_down_loading').hide();
                                $('#shut_down_success').show();
                                clearInterval(checkIsAlive);
                                $('#restart_loading').hide();
                                $('#restart_success').show();
                                setTimeout(function () {
                                    $('#refresh_message').show();
                                    window.location = '/' + SICKRAGE.srDefaultPage + '/';
                                }, 25000);
                            }
                        },
                        error: function (error) {
                            $('#restart_message').show();
                        }
                    });
                }, 100);
            },

            new_show: {
                init: function () {
                    $("#addShowForm").steps({
                        bodyTag: "section",
                        transitionEffect: "fade",
                        stepsOrientation: "vertical",
                        onStepChanging: function (event, currentIndex, newIndex) {
                            var show_name;
                            if (currentIndex > newIndex) {
                                return true;
                            }

                            SICKRAGE.home.add_show_options();
                            SICKRAGE.root_dirs.init();
                            SICKRAGE.quality_chooser.init();


                            // if they've picked a radio button then use that
                            if ($('input:radio[name=whichSeries]:checked').length) {
                                show_name = $('input:radio[name=whichSeries]:checked').val().split('|')[4];
                            }
                            // if we provided a show in the hidden field, use that
                            else if ($('input:hidden[name=whichSeries]').length && $('input:hidden[name=whichSeries]').val().length) {
                                show_name = $('#providedName').val();
                            } else {
                                show_name = '';
                            }

                            if (show_name.length) {
                                SICKRAGE.home.update_bwlist(show_name);
                                return true;
                            }
                        },
                        onFinished: function (event, currentIndex) {
                            SICKRAGE.home.generate_bwlist();
                            $(this).submit();
                        }
                    });

                    if ($('input:hidden[name=whichSeries]').length && $('#fullShowPath').length) {
                        $("#addShowForm").steps('getStep', '1');
                    }

                    $('#searchName').on('click', function () {
                        $('#searchName').prop('disabled', true);
                        SICKRAGE.home.new_show.searchIndexers();
                        $('#searchName').prop('disabled', false);
                    });

                    $('#skipShowButton').on('click', function () {
                        $('#skipShow').val('1');
                        $('#addShowForm').submit();
                    });

                    $('#nameToSearch').focus();

                    $('#indexerLang').bfhlanguages({
                        language: SICKRAGE.getMeta('sickrage.DEFAULT_LANGUAGE'),
                        available: SICKRAGE.getMeta('sickrage.LANGUAGES')
                    });
                },

                searchIndexers: function () {
                    if (!$('#nameToSearch').val().length) {
                        return;
                    }

                    var searchingFor = '<b>' + $('#nameToSearch').val().trim() + '</b> on ' + $('#providedIndexer option:selected').text() + '<br/>';
                    $('#messages').empty().html('<img id="searchingAnim" src="/images/loading32' + SICKRAGE.themeSpinner + '.gif" height="24" width="24" /> searching for ' + searchingFor);

                    $.ajax({
                        url: '/home/addShows/searchIndexersForShowName',
                        data: {
                            'search_term': $('#nameToSearch').val().trim(),
                            'lang': $('#indexerLang').val(),
                            'indexer': $('#providedIndexer').val()
                        },
                        timeout: parseInt($('#indexer_timeout').val(), 10) * 1000,
                        dataType: 'json',
                        error: function () {
                            $('#messages').empty().html('search timed out, try again or try another indexer');
                        },
                        success: function (data) {
                            var firstResult = true;
                            var resultStr = '<legend class="legend">Search Results:</legend>\n';
                            var checked = '';

                            if (data.results.length === 0) {
                                resultStr += '<b>No results found, try a different search or language.</b>';
                            } else {
                                $.each(data.results, function (index, obj) {
                                    if (firstResult) {
                                        checked = ' checked';
                                        firstResult = false;
                                    } else {
                                        checked = '';
                                    }

                                    var whichSeries = obj.join('|');

                                    resultStr += '<input type="radio" class="pull-left" id="whichSeries" name="whichSeries" value="' + whichSeries.replace(/"/g, "") + '"' + checked + ' /> ';
                                    resultStr += '<a href="' + SICKRAGE.anon_url(obj[2] + obj[3] + '&lid=' + data.langid || 7) + '" onclick=\"window.open(this.href, \'_blank\'); return false;\" ><b>' + obj[4] + '</b></a>';

                                    if (obj[5] !== null) {
                                        var startDate = new Date(obj[5]);
                                        var today = new Date();
                                        if (startDate > today) {
                                            resultStr += ' (will debut on ' + obj[5] + ')';
                                        } else {
                                            resultStr += ' (started on ' + obj[5] + ')';
                                        }
                                    }

                                    if (obj[0] !== null) {
                                        resultStr += ' [' + obj[0] + ']';
                                    }

                                    resultStr += '<br/>';
                                });
                                resultStr += '</ul>';
                            }
                            resultStr += '<br/>';

                            $('#messages').html(resultStr);
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

                    $.get('/config/general/saveAddShowDefaults', {
                        defaultStatus: $('#statusSelect').val(),
                        anyQualities: anyQualArray.join(','),
                        bestQualities: bestQualArray.join(','),
                        defaultFlattenFolders: $('#flatten_folders').prop('checked'),
                        subtitles: $('#subtitles').prop('checked'),
                        anime: $('#anime').prop('checked'),
                        scene: $('#scene').prop('checked'),
                        defaultStatusAfter: $('#statusSelectAfter').val(),
                        archive: $('#archive').prop('checked')
                    });

                    $(this).attr('disabled', true);
                    new PNotify({
                        title: 'Saved Defaults',
                        text: 'Your "add show" defaults have been set to your current selections.',
                        shadow: false
                    });
                });

                $('#statusSelect, #qualityPreset, #flatten_folders, #anyQualities, #bestQualities, #subtitles, #scene, #anime, #statusSelectAfter, #archive').change(function () {
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
                        $.getJSON('/home/fetch_releasegroups', {'show_name': show_name}, function (data) {
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
            }
        },

        config: {
            init: function () {
                $('#configForm').ajaxForm({
                    beforeSubmit: function () {
                        $('.config_submitter .config_submitter_refresh').each(function () {
                            $(this).attr("disabled", "disabled");
                            $(this).after('<span>' + SICKRAGE.loading + ' Saving...</span>');
                            $(this).hide();
                        });
                    },
                    success: function () {
                        setTimeout(function () {
                            "use strict";
                            $('.config_submitter').each(function () {
                                $(this).removeAttr("disabled");
                                $.next().remove();
                                $(this).show();
                            });

                            $('.config_submitter_refresh').each(function () {
                                $(this).removeAttr("disabled");
                                $.next().remove();
                                $(this).show();
                                window.location.reload();
                            });

                            $('#email_show').trigger('notify');
                        }, 2000);
                    }
                });
            },

            general: function () {
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

                $('#log_dir').fileBrowser({title: 'Select log file folder location'});


                $(".enabler").each(function () {
                    if (!$(this).prop('checked')) {
                        $('#content_' + $(this).attr('id')).hide();
                    }
                });

                $(".enabler").on('click', function () {
                    if ($(this).prop('checked')) {
                        $('#content_' + $(this).attr('id')).fadeIn("fast", "linear");
                    } else {
                        $('#content_' + $(this).attr('id')).fadeOut("fast", "linear");
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
                    $.get('/config/general/generateApiKey',
                        function (data) {
                            if (data.error !== undefined) {
                                alert(data.error);
                                return;
                            }
                            $('#api_key').val(data);
                        });
                });

                $('#branchCheckout').on('click', function () {
                    window.location.href = '/home/branchCheckout?branch=' + $("#branchVersion").val();
                });

                $('#google_link').on('click', function () {
                    if (localStorage.getItem('google_token_type') === null || localStorage.getItem('google_access_token') === null) {
                        SICKRAGE.google.login();
                    } else {
                        SICKRAGE.google.logout();
                    }
                });

                if (localStorage.getItem('google_token_type') === null || localStorage.getItem('google_access_token') === null) {
                    $('#google_link').prop('value', 'Link');
                } else {
                    $('#google_link').prop('value', 'Unlink');
                }
            },

            subtitles: {
                init: function () {
                    $('#subtitles_dir').fileBrowser({title: 'Select Subtitles Download Directory'});

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
                        var toAdd = '<li class="ui-state-default" id="' + id + '"> <input type="checkbox" id="enable_' + id + '" class="service_enabler" CHECKED> <a href="' + SICKRAGE.anon_url(url) + '" class="imgLink" target="_new"><img src="/images/services/newznab.gif" alt="' + name + '" width="16" height="16"></a> ' + name + '</li>';

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
                        $('#testSABnzbd_result').html(SICKRAGE.loading);
                        var sab_host = $('#sab_host').val();
                        var sab_username = $('#sab_username').val();
                        var sab_password = $('#sab_password').val();
                        var sab_apiKey = $('#sab_apikey').val();

                        $.get('/home/testSABnzbd', {
                                'host': sab_host,
                                'username': sab_username,
                                'password': sab_password,
                                'apikey': sab_apiKey
                            },
                            function (data) {
                                $('#testSABnzbd_result').html(data);
                            });
                    });

                    $('#use_torrents').click(function () {
                        SICKRAGE.config.search.toggleTorrentTitle();
                    });

                    $('#test_torrent').click(function () {
                        $('#test_torrent_result').html(SICKRAGE.loading);
                        var torrent_method = $('#torrent_method :selected').val();
                        var torrent_host = $('#torrent_host').val();
                        var torrent_username = $('#torrent_username').val();
                        var torrent_password = $('#torrent_password').val();

                        $.get('/home/testTorrent', {
                                'torrent_method': torrent_method,
                                'host': torrent_host,
                                'username': torrent_username,
                                'password': torrent_password
                            },
                            function (data) {
                                $('#test_torrent_result').html(data);
                            });
                    });

                    $('#torrent_host').change(SICKRAGE.config.search.rtorrentScgi);


                    $('#nzb_dir').fileBrowser({title: 'Select .nzb blackhole/watch location'});
                    $('#torrent_dir').fileBrowser({title: 'Select .torrent blackhole/watch location'});
                    $('#torrent_path').fileBrowser({title: 'Select .torrent download location'});
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
                    $('#testSABnzbd').hide();
                    $('#testSABnzbd_result').hide();
                    $('#nzbget_settings').hide();

                    if ($('#nzb_method').val().toLowerCase() === 'blackhole') {
                        $('#blackhole_settings').show();
                    } else if ($('#nzb_method').val().toLowerCase() === 'nzbget') {
                        $('#nzbget_settings').show();
                    } else {
                        $('#sabnzbd_settings').show();
                        $('#testSABnzbd').show();
                        $('#testSABnzbd_result').show();
                    }
                },

                torrentMethodHandler: function () {
                    $('#options_torrent_clients').hide();
                    $('#options_torrent_blackhole').hide();

                    var selectedProvider = $('#torrent_method').val(),
                        host = ' host:port',
                        username = ' username',
                        password = ' password',
                        client = '',
                        optionPanel = '#options_torrent_blackhole',
                        rpcurl = ' RPC URL';

                    $('#torrent_method_icon').removeClass(function (index, css) {
                        return (css.match(/(^|\s)add-client-icon-\S+/g) || []).join(' ');
                    });
                    $('#torrent_method_icon').addClass('add-client-icon-' + selectedProvider.replace('_', '-'));

                    if (selectedProvider.toLowerCase() !== 'blackhole') {
                        $('#label_warning_deluge').hide();
                        $('#label_anime_warning_deluge').hide();
                        $('#host_desc_torrent').show();
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
                            $('#torrent_seed_time_label').text('Minimum seeding time is');
                            $('#torrent_seed_time_option').show();
                            $('#host_desc_torrent').text('URL to your uTorrent client (e.g. http://localhost:8000)');
                        } else if (selectedProvider.toLowerCase() === 'transmission') {
                            client = 'Transmission';
                            $('#torrent_seed_time_label').text('Stop seeding when inactive for');
                            $('#torrent_seed_time_option').show();
                            $('#torrent_high_bandwidth_option').show();
                            $('#torrent_label_option').hide();
                            $('#torrent_label_anime_option').hide();
                            $('#torrent_rpcurl_option').show();
                            $('#host_desc_torrent').text('URL to your Transmission client (e.g. http://localhost:9091)');
                        } else if (selectedProvider.toLowerCase() === 'deluge') {
                            client = 'Deluge';
                            $('#torrent_verify_cert_option').show();
                            $('#torrent_verify_deluge').show();
                            $('#torrent_verify_rtorrent').hide();
                            $('#label_warning_deluge').show();
                            $('#label_anime_warning_deluge').show();
                            $('#torrent_username_option').hide();
                            $('#torrent_username').prop('value', '');
                            $('#host_desc_torrent').text('URL to your Deluge client (e.g. http://localhost:8112)');
                        } else if (selectedProvider.toLowerCase() === 'deluged') {
                            client = 'Deluge';
                            $('#torrent_verify_cert_option').hide();
                            $('#torrent_verify_deluge').hide();
                            $('#torrent_verify_rtorrent').hide();
                            $('#label_warning_deluge').show();
                            $('#label_anime_warning_deluge').show();
                            $('#torrent_username_option').show();
                            $('#host_desc_torrent').text('IP or Hostname of your Deluge Daemon (e.g. scgi://localhost:58846)');
                        } else if (selectedProvider.toLowerCase() === 'download_station') {
                            client = 'Synology DS';
                            $('#torrent_label_option').hide();
                            $('#torrent_label_anime_option').hide();
                            $('#torrent_paused_option').hide();
                            $('#torrent_path_option').find('.fileBrowser').hide();
                            $('#host_desc_torrent').text('URL to your Synology DS client (e.g. http://localhost:5000)');
                            $('#path_synology').show();
                        } else if (selectedProvider.toLowerCase() === 'rtorrent') {
                            client = 'rTorrent';
                            $('#torrent_paused_option').hide();
                            $('#host_desc_torrent').text('URL to your rTorrent client (e.g. scgi://localhost:5000 <br> or https://localhost/rutorrent/plugins/httprpc/action.php)');
                            $('#torrent_verify_cert_option').show();
                            $('#torrent_verify_deluge').hide();
                            $('#torrent_verify_rtorrent').show();
                            $('#torrent_auth_type_option').show();
                        } else if (selectedProvider.toLowerCase() === 'qbittorrent') {
                            client = 'qbittorrent';
                            $('#torrent_path_option').hide();
                            $('#label_warning_qbittorrent').show();
                            $('#label_anime_warning_qbittorrent').show();
                            $('#host_desc_torrent').text('URL to your qbittorrent client (e.g. http://localhost:8080)');
                        } else if (selectedProvider.toLowerCase() === 'mlnet') {
                            client = 'mlnet';
                            $('#torrent_path_option').hide();
                            $('#torrent_label_option').hide();
                            $('#torrent_verify_cert_option').hide();
                            $('#torrent_verify_deluge').hide();
                            $('#torrent_verify_rtorrent').hide();
                            $('#torrent_label_anime_option').hide();
                            $('#torrent_paused_option').hide();
                            $('#host_desc_torrent').text('URL to your MLDonkey (e.g. http://localhost:4080)');
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
                            $('#host_desc_torrent').text('URL to your putio client (e.g. http://localhost:8080)');
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
                    var selectedProvider = $('#torrent_method :selected').val();

                    if (selectedProvider.toLowerCase() === 'rtorrent') {
                        var hostname = $('#torrent_host').prop('value');
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
                            $('#unpack').qtip('toggle', false);
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
                        $('#naming_key').toggle();
                    });
                    $('#show_naming_abd_key').on('click', function () {
                        $('#naming_abd_key').toggle();
                    });
                    $('#show_naming_sports_key').on('click', function () {
                        $('#naming_sports_key').toggle();
                    });
                    $('#show_naming_anime_key').on('click', function () {
                        $('#naming_anime_key').toggle();
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
                    $('img[title]').qtip({
                        position: {
                            viewport: $(window),
                            at: 'bottom center',
                            my: 'top right'
                        },
                        style: {
                            tip: {
                                corner: true,
                                method: 'polygon'
                            },
                            classes: 'qtip-shadow qtip-dark'
                        }
                    });
                    $('i[title]').qtip({
                        position: {
                            viewport: $(window),
                            at: 'top center',
                            my: 'bottom center'
                        },
                        style: {
                            tip: {
                                corner: true,
                                method: 'polygon'
                            },
                            classes: 'qtip-rounded qtip-shadow ui-tooltip-sb'
                        }
                    });
                    $('.custom-pattern,#unpack').qtip({
                        content: 'validating...',
                        show: {
                            event: false,
                            ready: false
                        },
                        hide: false,
                        position: {
                            viewport: $(window),
                            at: 'center left',
                            my: 'center right'
                        },
                        style: {
                            tip: {
                                corner: true,
                                method: 'polygon'
                            },
                            classes: 'qtip-rounded qtip-shadow qtip-red'
                        }
                    });

                    $('#tv_download_dir').fileBrowser({title: 'Select TV Download Directory'});
                },

                typewatch: function () {
                    var timer = 0;
                    return function (callback, ms) {
                        clearTimeout(timer);
                        timer = setTimeout(callback, ms);
                    };
                },

                israr_supported: function () {
                    $.get('/config/postProcessing/isRarSupported', function (data) {
                        if (data !== "supported") {
                            $('#unpack').qtip('option', {
                                'content.text': 'Unrar Executable not found.',
                                'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                            });
                            $('#unpack').qtip('toggle', true);
                            $('#unpack').css('background-color', '#FFFFDD');
                        }
                    });
                },

                fill_examples: function () {
                    var pattern = $('#naming_pattern').val();
                    var multi = $('#naming_multi_ep :selected').val();
                    var anime_type = $('input[name="naming_anime"]:checked').val();

                    $.get('/config/postProcessing/testNaming', {pattern: pattern, anime_type: 3}, function (data) {
                        if (data) {
                            $('#naming_example').text(data + '.ext');
                            $('#naming_example_div').show();
                        } else {
                            $('#naming_example_div').hide();
                        }
                    });

                    $.get('/config/postProcessing/testNaming', {
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

                    $.get('/config/postProcessing/isNamingValid', {
                        pattern: pattern,
                        multi: multi,
                        anime_type: anime_type
                    }, function (data) {
                        if (data === "invalid") {
                            $('#naming_pattern').qtip('option', {
                                'content.text': 'This pattern is invalid.',
                                'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                            });
                            $('#naming_pattern').qtip('toggle', true);
                            $('#naming_pattern').css('background-color', '#FFDDDD');
                        } else if (data === "seasonfolders") {
                            $('#naming_pattern').qtip('option', {
                                'content.text': 'This pattern would be invalid without the folders, using it will force "Flatten" off for all shows.',
                                'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                            });
                            $('#naming_pattern').qtip('toggle', true);
                            $('#naming_pattern').css('background-color', '#FFFFDD');
                        } else {
                            $('#naming_pattern').qtip('option', {
                                'content.text': 'This pattern is valid.',
                                'style.classes': 'qtip-rounded qtip-shadow qtip-green'
                            });
                            $('#naming_pattern').qtip('toggle', false);
                            $('#naming_pattern').css('background-color', '#FFFFFF');
                        }
                    });
                },

                fill_abd_examples: function () {
                    var pattern = $('#naming_abd_pattern').val();

                    $.get('/config/postProcessing/testNaming', {pattern: pattern, abd: 'True'}, function (data) {
                        if (data) {
                            $('#naming_abd_example').text(data + '.ext');
                            $('#naming_abd_example_div').show();
                        } else {
                            $('#naming_abd_example_div').hide();
                        }
                    });

                    $.get('/config/postProcessing/isNamingValid', {
                        pattern: pattern,
                        abd: 'True'
                    }, function (data) {
                        if (data === "invalid") {
                            $('#naming_abd_pattern').qtip('option', {
                                'content.text': 'This pattern is invalid.',
                                'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                            });
                            $('#naming_abd_pattern').qtip('toggle', true);
                            $('#naming_abd_pattern').css('background-color', '#FFDDDD');
                        } else if (data === "seasonfolders") {
                            $('#naming_abd_pattern').qtip('option', {
                                'content.text': 'This pattern would be invalid without the folders, using it will force "Flatten" off for all shows.',
                                'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                            });
                            $('#naming_abd_pattern').qtip('toggle', true);
                            $('#naming_abd_pattern').css('background-color', '#FFFFDD');
                        } else {
                            $('#naming_abd_pattern').qtip('option', {
                                'content.text': 'This pattern is valid.',
                                'style.classes': 'qtip-rounded qtip-shadow qtip-green'
                            });
                            $('#naming_abd_pattern').qtip('toggle', false);
                            $('#naming_abd_pattern').css('background-color', '#FFFFFF');
                        }
                    });
                },

                fill_sports_examples: function () {
                    var pattern = $('#naming_sports_pattern').val();

                    $.get('/config/postProcessing/testNaming', {
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

                    $.get('/config/postProcessing/isNamingValid', {
                        pattern: pattern,
                        sports: 'True'
                    }, function (data) {
                        if (data === "invalid") {
                            $('#naming_sports_pattern').qtip('option', {
                                'content.text': 'This pattern is invalid.',
                                'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                            });
                            $('#naming_sports_pattern').qtip('toggle', true);
                            $('#naming_sports_pattern').css('background-color', '#FFDDDD');
                        } else if (data === "seasonfolders") {
                            $('#naming_sports_pattern').qtip('option', {
                                'content.text': 'This pattern would be invalid without the folders, using it will force "Flatten" off for all shows.',
                                'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                            });
                            $('#naming_sports_pattern').qtip('toggle', true);
                            $('#naming_sports_pattern').css('background-color', '#FFFFDD');
                        } else {
                            $('#naming_sports_pattern').qtip('option', {
                                'content.text': 'This pattern is valid.',
                                'style.classes': 'qtip-rounded qtip-shadow qtip-green'
                            });
                            $('#naming_sports_pattern').qtip('toggle', false);
                            $('#naming_sports_pattern').css('background-color', '#FFFFFF');
                        }
                    });
                },

                fill_anime_examples: function () {
                    var pattern = $('#naming_anime_pattern').val();
                    var multi = $('#naming_anime_multi_ep :selected').val();
                    var anime_type = $('input[name="naming_anime"]:checked').val();

                    $.get('/config/postProcessing/testNaming', {
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

                    $.get('/config/postProcessing/testNaming', {
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

                    $.get('/config/postProcessing/isNamingValid', {
                        pattern: pattern,
                        multi: multi,
                        anime_type: anime_type
                    }, function (data) {
                        if (data === "invalid") {
                            $('#naming_pattern').qtip('option', {
                                'content.text': 'This pattern is invalid.',
                                'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                            });
                            $('#naming_pattern').qtip('toggle', true);
                            $('#naming_pattern').css('background-color', '#FFDDDD');
                        } else if (data === "seasonfolders") {
                            $('#naming_pattern').qtip('option', {
                                'content.text': 'This pattern would be invalid without the folders, using it will force "Flatten" off for all shows.',
                                'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                            });
                            $('#naming_pattern').qtip('toggle', true);
                            $('#naming_pattern').css('background-color', '#FFFFDD');
                        } else {
                            $('#naming_pattern').qtip('option', {
                                'content.text': 'This pattern is valid.',
                                'style.classes': 'qtip-rounded qtip-shadow qtip-green'
                            });
                            $('#naming_pattern').qtip('toggle', false);
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
                            $('#testGrowl-result').html('Please fill out the necessary fields above.');
                            $('#growl_host').addClass('warning');
                            return;
                        }
                        $('#growl_host').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testGrowl-result').html(SICKRAGE.loading);
                        $.get('/home/testGrowl', {'host': growl_host, 'password': growl_password})
                            .done(function (data) {
                                $('#testGrowl-result').html(data);
                                $('#testGrowl').prop('disabled', false);
                            });
                    });

                    $('#testProwl').click(function () {
                        var prowl_api = $.trim($('#prowl_api').val());
                        var prowl_priority = $('#prowl_priority').val();
                        if (!prowl_api) {
                            $('#testProwl-result').html('Please fill out the necessary fields above.');
                            $('#prowl_api').addClass('warning');
                            return;
                        }
                        $('#prowl_api').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testProwl-result').html(SICKRAGE.loading);
                        $.get('/home/testProwl', {
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
                            $('#testKODI-result').html('Please fill out the necessary fields above.');
                            $('#kodi_host').addClass('warning');
                            return;
                        }
                        $('#kodi_host').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testKODI-result').html(SICKRAGE.loading);
                        $.get('/home/testKODI', {
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
                            $('#testPMC-result').html('Please fill out the necessary fields above.');
                            $('#plex_host').addClass('warning');
                            return;
                        }
                        $('#plex_host').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testPMC-result').html(SICKRAGE.loading);
                        $.get('/home/testPMC', {
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
                            $('#testPMS-result').html('Please fill out the necessary fields above.');
                            $('#plex_server_host').addClass('warning');
                            return;
                        }
                        $('#plex_server_host').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testPMS-result').html(SICKRAGE.loading);
                        $.get('/home/testPMS', {
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
                            $('#testEMBY-result').html('Please fill out the necessary fields above.');
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
                        $('#testEMBY-result').html(SICKRAGE.loading);
                        $.get('/home/testEMBY', {
                            'host': emby_host,
                            'emby_apikey': emby_apikey
                        }).done(function (data) {
                            $('#testEMBY-result').html(data);
                            $('#testEMBY').prop('disabled', false);
                        });
                    });

                    $('#testBoxcar').click(function () {
                        var boxcar_username = $.trim($('#boxcar_username').val());
                        if (!boxcar_username) {
                            $('#testBoxcar-result').html('Please fill out the necessary fields above.');
                            $('#boxcar_username').addClass('warning');
                            return;
                        }
                        $('#boxcar_username').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testBoxcar-result').html(SICKRAGE.loading);
                        $.get('/home/testBoxcar', {'username': boxcar_username}).done(function (data) {
                            $('#testBoxcar-result').html(data);
                            $('#testBoxcar').prop('disabled', false);
                        });
                    });

                    $('#testBoxcar2').click(function () {
                        var boxcar2_accesstoken = $.trim($('#boxcar2_accesstoken').val());
                        if (!boxcar2_accesstoken) {
                            $('#testBoxcar2-result').html('Please fill out the necessary fields above.');
                            $('#boxcar2_accesstoken').addClass('warning');
                            return;
                        }
                        $('#boxcar2_accesstoken').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testBoxcar2-result').html(SICKRAGE.loading);
                        $.get('/home/testBoxcar2', {'accesstoken': boxcar2_accesstoken}).done(function (data) {
                            $('#testBoxcar2-result').html(data);
                            $('#testBoxcar2').prop('disabled', false);
                        });
                    });

                    $('#testPushover').click(function () {
                        var pushover_userkey = $('#pushover_userkey').val();
                        var pushover_apikey = $('#pushover_apikey').val();
                        if (!pushover_userkey || !pushover_apikey) {
                            $('#testPushover-result').html('Please fill out the necessary fields above.');
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
                        $('#testPushover-result').html(SICKRAGE.loading);
                        $.get('/home/testPushover', {
                            'userKey': pushover_userkey,
                            'apiKey': pushover_apikey
                        }).done(function (data) {
                            $('#testPushover-result').html(data);
                            $('#testPushover').prop('disabled', false);
                        });
                    });

                    $('#testLibnotify').click(function () {
                        $('#testLibnotify-result').html(SICKRAGE.loading);
                        $.get('/home/testLibnotify', function (data) {
                            $('#testLibnotify-result').html(data);
                        });
                    });

                    $('#twitterStep1').click(function () {
                        $('#testTwitter-result').html(SICKRAGE.loading);
                        $.get('/home/twitterStep1', function (data) {
                            window.open(data);
                        }).done(function () {
                            $('#testTwitter-result').html('<b>Step1:</b> Confirm Authorization');
                        });
                    });

                    $('#twitterStep2').click(function () {
                        var twitter_key = $.trim($('#twitter_key').val());
                        if (!twitter_key) {
                            $('#testTwitter-result').html('Please fill out the necessary fields above.');
                            $('#twitter_key').addClass('warning');
                            return;
                        }
                        $('#twitter_key').removeClass('warning');
                        $('#testTwitter-result').html(SICKRAGE.loading);
                        $.get('/home/twitterStep2', {'key': twitter_key}, function (data) {
                            $('#testTwitter-result').html(data);
                        });
                    });

                    $('#testTwitter').click(function () {
                        $.get('/home/testTwitter', function (data) {
                            $('#testTwitter-result').html(data);
                        });
                    });

                    $('#settingsNMJ').click(function () {
                        if (!$('#nmj_host').val()) {
                            alert('Please fill in the Popcorn IP address');
                            $('#nmj_host').focus();
                            return;
                        }
                        $('#testNMJ-result').html(SICKRAGE.loading);
                        var nmj_host = $('#nmj_host').val();

                        $.get('/home/settingsNMJ', {'host': nmj_host}, function (data) {
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
                            $('#testNMJ-result').html('Please fill out the necessary fields above.');
                            $('#nmj_host').addClass('warning');
                            return;
                        }
                        $('#nmj_host').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testNMJ-result').html(SICKRAGE.loading);
                        $.get('/home/testNMJ', {
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
                            alert('Please fill in the Popcorn IP address');
                            $('#nmjv2_host').focus();
                            return;
                        }
                        $('#testNMJv2-result').html(SICKRAGE.loading);
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
                        $.get('/home/settingsNMJv2', {
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
                            $('#testNMJv2-result').html('Please fill out the necessary fields above.');
                            $('#nmjv2_host').addClass('warning');
                            return;
                        }
                        $('#nmjv2_host').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testNMJv2-result').html(SICKRAGE.loading);
                        $.get('/home/testNMJv2', {'host': nmjv2_host}).done(function (data) {
                            $('#testNMJv2-result').html(data);
                            $('#testNMJv2').prop('disabled', false);
                        });
                    });

                    $('#testFreeMobile').click(function () {
                        var freemobile_id = $.trim($('#freemobile_id').val());
                        var freemobile_apikey = $.trim($('#freemobile_apikey').val());
                        if (!freemobile_id || !freemobile_apikey) {
                            $('#testFreeMobile-result').html('Please fill out the necessary fields above.');
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
                        $('#testFreeMobile-result').html(SICKRAGE.loading);
                        $.get('/home/testFreeMobile', {
                            'freemobile_id': freemobile_id,
                            'freemobile_apikey': freemobile_apikey
                        }).done(function (data) {
                            $('#testFreeMobile-result').html(data);
                            $('#testFreeMobile').prop('disabled', false);
                        });
                    });

                    $('#TraktGetPin').click(function () {
                        var trakt_pin_url = $('#trakt_pin_url').val();
                        window.open(trakt_pin_url, "popUp", "toolbar=no, scrollbars=no, resizable=no, top=200, left=200, width=650, height=550");
                        $('#trakt_pin').removeClass('hide');
                    });

                    $('#trakt_pin').on('keyup change', function () {
                        var trakt_pin = $('#trakt_pin').val();

                        if (trakt_pin.length !== 0) {
                            $('#TraktGetPin').addClass('hide');
                            $('#authTrakt').removeClass('hide');
                        } else {
                            $('#TraktGetPin').removeClass('hide');
                            $('#authTrakt').addClass('hide');
                        }
                    });

                    $('#authTrakt').click(function () {
                        var trakt_pin = $('#trakt_pin').val();
                        if (trakt_pin.length !== 0) {
                            $.get('/home/getTraktToken', {"trakt_pin": trakt_pin}).done(function (data) {
                                $('#testTrakt-result').html(data);
                                $('#authTrakt').addClass('hide');
                                $('#trakt_pin').addClass('hide');
                                $('#TraktGetPin').addClass('hide');
                            });
                        }
                    });

                    $('#testTrakt').click(function () {
                        var trakt_username = $.trim($('#trakt_username').val());
                        var trakt_trending_blacklist = $.trim($('#trakt_blacklist_name').val());
                        if (!trakt_username) {
                            $('#testTrakt-result').html('Please fill out the necessary fields above.');
                            if (!trakt_username) {
                                $('#trakt_username').addClass('warning');
                            } else {
                                $('#trakt_username').removeClass('warning');
                            }
                            return;
                        }

                        if (/\s/g.test(trakt_trending_blacklist)) {
                            $('#testTrakt-result').html('Check blacklist name; the value need to be a trakt slug');
                            $('#trakt_blacklist_name').addClass('warning');
                            return;
                        }
                        $('#trakt_username').removeClass('warning');
                        $('#trakt_blacklist_name').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testTrakt-result').html(SICKRAGE.loading);
                        $.get('/home/testTrakt', {
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
                        status.html(SICKRAGE.loading);
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
                            err += '<li style="color: red;">You must specify an SMTP hostname!</li>';
                        }
                        if (port === null) {
                            err += '<li style="color: red;">You must specify an SMTP port!</li>';
                        } else if (port.match(/^\d+$/) === null || parseInt(port, 10) > 65535) {
                            err += '<li style="color: red;">SMTP port must be between 0 and 65535!</li>';
                        }
                        if (err.length > 0) {
                            err = '<ol>' + err + '</ol>';
                            status.html(err);
                        } else {
                            to = prompt('Enter an email address to send the test to:', null);
                            if (to === null || to.length === 0 || to.match(/.*@.*/) === null) {
                                status.html('<p style="color: red;">You must provide a recipient email address!</p>');
                            } else {
                                $.get('/home/testEmail', {
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
                            $('#testNMA-result').html('Please fill out the necessary fields above.');
                            $('#nma_api').addClass('warning');
                            return;
                        }
                        $('#nma_api').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testNMA-result').html(SICKRAGE.loading);
                        $.get('/home/testNMA', {
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
                            $('#testPushalot-result').html('Please fill out the necessary fields above.');
                            $('#pushalot_authorizationtoken').addClass('warning');
                            return;
                        }
                        $('#pushalot_authorizationtoken').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testPushalot-result').html(SICKRAGE.loading);
                        $.get('/home/testPushalot', {'authorizationToken': pushalot_authorizationtoken}).done(function (data) {
                            $('#testPushalot-result').html(data);
                            $('#testPushalot').prop('disabled', false);
                        });
                    });

                    $('#testPushbullet').click(function () {
                        var pushbullet_api = $.trim($('#pushbullet_api').val());
                        if (!pushbullet_api) {
                            $('#testPushbullet-result').html('Please fill out the necessary fields above.');
                            $('#pushbullet_api').addClass('warning');
                            return;
                        }
                        $('#pushbullet_api').removeClass('warning');
                        $(this).prop('disabled', true);
                        $('#testPushbullet-result').html(SICKRAGE.loading);
                        $.get('/home/testPushbullet', {'api': pushbullet_api}).done(function (data) {
                            $('#testPushbullet-result').html(data);
                            $('#testPushbullet').prop('disabled', false);
                        });
                    });

                    $('#getPushbulletDevices').click(function () {
                        SICKRAGE.config.notifications.get_pushbullet_devices("Device list updated. Please choose a device to push to.");
                    });

                    // we have to call this function on dom ready to create the devices select
                    SICKRAGE.config.notifications.get_pushbullet_devices();

                    $('#email_show').on('change', function () {
                        var key = parseInt($('#email_show').val(), 10);
                        $.getJSON("/home/loadShowNotifyLists", function (notifyData) {
                            if (notifyData._size > 0) {
                                $('#email_show_list').val(key >= 0 ? notifyData[key.toString()].list : '');
                            }
                        });
                    });

                    $('#prowl_show').on('change', function () {
                        var key = parseInt($('#prowl_show').val(), 10);
                        $.getJSON("/home/loadShowNotifyLists", function (notifyData) {
                            if (notifyData._size > 0) {
                                $('#prowl_show_list').val(key >= 0 ? notifyData[key.toString()].prowl_notify_list : '');
                            }
                        });
                    });

                    // Load the per show notify lists everytime this page is loaded
                    SICKRAGE.config.notifications.load_show_notify_lists();

                    $('#email_show_save').click(function () {
                        $.post("/home/saveShowNotifyList", {
                            show: $('#email_show').val(),
                            emails: $('#email_show_list').val()
                        }, function () {
                            // Reload the per show notify lists to reflect changes
                            SICKRAGE.config.notifications.load_show_notify_lists();
                        });
                    });

                    // show instructions for plex when enabled
                    $('#use_plex').click(function () {
                        if ($(this).is(':checked')) {
                            $('.plexinfo').removeClass('hide');
                        } else {
                            $('.plexinfo').addClass('hide');
                        }
                    });
                },

                get_pushbullet_devices: function (msg) {
                    if (msg) {
                        $('#testPushbullet-result').html(SICKRAGE.loading);
                    }

                    var pushbullet_api = $("#pushbullet_api").val();

                    if (!pushbullet_api) {
                        $('#testPushbullet-result').html("You didn't supply a Pushbullet api key");
                        $("#pushbullet_api").focus();
                        return false;
                    }

                    $.get("/home/getPushbulletDevices", {'api': pushbullet_api}, function (data) {
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
                        $('#testPushbullet-result').html("Don't forget to save your new pushbullet settings.");
                    });
                },

                load_show_notify_lists: function () {
                    $.getJSON("/home/loadShowNotifyLists", function (list) {
                        var html, s;
                        if (list._size === 0) {
                            return;
                        }

                        // Convert the 'list' object to a js array of objects so that we can sort it
                        var _list = [];
                        for (s in list) {
                            if (list.hasOwnProperty(s) && s.charAt(0) !== '_') {
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
                            if (sortedList.hasOwnProperty(s) && sortedList[s].id && sortedList[s].name) {
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
                    $('#Backup-result').html(SICKRAGE.loading);
                    var backupDir = $("#backupDir").val();
                    $.get("/config/backuprestore/backup", {'backupDir': backupDir})
                        .done(function (data) {
                            $('#Backup-result').html(data);
                            $("#Backup").attr("disabled", false);
                        });
                });

                $('#Restore').click(function () {
                    $("#Restore").attr("disabled", true);
                    $('#Restore-result').html(SICKRAGE.loading);
                    var backupFile = $("#backupFile").val();
                    $.get("/config/backuprestore/restore", {'backupFile': backupFile})
                        .done(function (data) {
                            $('#Restore-result').html(data);
                            $("#Restore").attr("disabled", false);
                        });
                });

                $('#backupDir').fileBrowser({
                    title: 'Select backup folder to save to',
                    key: 'backupPath'
                });

                $('#backupFile').fileBrowser({
                    title: 'Select backup files to restore',
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
                        $.getJSON('/config/providers/canAddNewznabProvider', params, function (data) {
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
                        $.getJSON('/config/providers/canAddTorrentRssProvider', params, function (data) {
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

                    $(document).on('change', '.enabler', function () {
                        if ($(this).is(':checked')) {
                            $('.content_' + $(this).attr('id')).each(function () {
                                $(this).show();
                            });
                        } else {
                            $('.content_' + $(this).attr('id')).each(function () {
                                $(this).hide();
                            });
                        }
                    });

                    $(".enabler").each(function () {
                        if (!$(this).is(':checked')) {
                            $('.content_' + $(this).attr('id')).hide();
                        } else {
                            $('.content_' + $(this).attr('id')).show();
                        }
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
                    for(var newznab_id = 0; newznab_id < newznab_providers.length; newznab_id++) {
                        var newznab_provider = newznab_providers[newznab_id];
                        if (newznab_provider.length > 0) {
                            SICKRAGE.config.providers.addNewznabProvider.apply(this, newznab_provider.split('|'));
                        }
                    }

                    var torrentrss_providers = SICKRAGE.getMeta('TORRENTRSS_PROVIDERS').split('!!!');
                    for(var torrentrss_id = 0; torrentrss_id < torrentrss_providers.length; torrentrss_id++) {
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
                        console.log(rootObject.name + " while searching for: " + searchFor);
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

                    $(".updating_categories").wrapInner('<span>' + SICKRAGE.loading + ' Updating Categories ...</span>');
                    $.getJSON('/config/providers/getNewznabCategories', params, function (data) {
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
                        $('#editANewznabProvider').addOption(id, name);
                        SICKRAGE.config.providers.populateNewznabSection();
                    }

                    if ($('#provider_order_list > #' + id).length === 0 && showProvider !== 'false') {
                        $('#provider_order_list').append('<li class="ui-state-default" id="' + id + '"> <input type="checkbox" id="enable_' + id + '" class="provider_enabler" CHECKED> <a href="' + SICKRAGE.anon_url(url) + '" class="imgLink" target="_new"><img src="/images/providers/nzb.png" alt="' + name + '" width="16" height="16"></a> ' + name + '</li>');
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
                    $('#editANewznabProvider').removeOption(id);
                    SICKRAGE.config.providers.populateNewznabSection();
                    $('li').remove('#' + id);
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
                        $('#editATorrentRssProvider').addOption(id, name);
                        SICKRAGE.config.providers.populateTorrentRssSection();
                    }

                    if ($('#provider_order_list > #' + id).length === 0 && showProvider !== 'false') {
                        $('#provider_order_list').append('<li class="ui-state-default" id="' + id + '"> <input type="checkbox" id="enable_' + id + '" class="provider_enabler" CHECKED> <a href="' + SICKRAGE.anon_url(url) + '" class="imgLink" target="_new"><img src="/images/providers/torrent.png" alt="' + name + '" width="16" height="16"></a> ' + name + '</li>');
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
                    $('#editATorrentRssProvider').removeOption(id);
                    SICKRAGE.config.providers.populateTorrentRssSection();
                    $('li').remove('#' + id);
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
                        if (SICKRAGE.config.providers.newznabProviders.hasOwnProperty(newznab_id)) {
                            provStrings.push(
                                "newznab|" + SICKRAGE.config.providers.newznabProviders[newznab_id][1].join('|')
                            );
                        }
                    }

                    for (var torrentrss_id in SICKRAGE.config.providers.torrentRssProviders) {
                        if (SICKRAGE.config.providers.torrentRssProviders.hasOwnProperty(torrentrss_id)) {
                            provStrings.push(
                                "torrentrss|" + SICKRAGE.config.providers.torrentRssProviders[torrentrss_id].join('|')
                            );
                        }
                    }

                    $("#provider_strings").val(provStrings.join(' '));
                    $("#provider_order").val(finalArr.join(' '));

                    SICKRAGE.config.providers.refreshEditAProvider();
                },

                refreshEditAProvider: function () {
                    $('#provider-list').empty();

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
                        document.getElementsByClassName('component-desc')[0].innerHTML = "No providers available to configure.";
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
            },

            episode_statuses: function () {
                function makeRow(indexerId, season, episode, name, checked) {
                    var row = '';
                    row += ' <tr class="' + $('#row_class').val() + ' show-' + indexerId + '">';
                    row += '  <td class="tableleft" align="center"><input type="checkbox" class="' + indexerId + '-epcheck" name="' + indexerId + '-' + season + 'x' + episode + '"' + (checked ? ' checked' : '') + '></td>';
                    row += '  <td>' + season + 'x' + episode + '</td>';
                    row += '  <td class="tableright" style="width: 100%">' + name + '</td>';
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
                        $.getJSON('/manage/showEpisodeStatuses', {
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
                    sortList: [[1, 0]],
                    textExtraction: {
                        2: function (node) {
                            return $(node).find("span").text().toLowerCase();
                        },
                        3: function (node) {
                            return $(node).find("img").attr("alt");
                        },
                        4: function (node) {
                            return $(node).find("img").attr("alt");
                        },
                        5: function (node) {
                            return $(node).find("img").attr("alt");
                        },
                        6: function (node) {
                            return $(node).find("img").attr("alt");
                        },
                        7: function (node) {
                            return $(node).find("img").attr("alt");
                        },
                        8: function (node) {
                            return $(node).find("img").attr("alt");
                        },
                        9: function (node) {
                            return $(node).find("img").attr("alt");
                        }
                    },
                    widgets: ['zebra'],
                    headers: {
                        0: {sorter: false},
                        1: {sorter: 'showNames'},
                        2: {sorter: 'quality'},
                        3: {sorter: 'sports'},
                        4: {sorter: 'scene'},
                        5: {sorter: 'anime'},
                        6: {sorter: 'flatfold'},
                        7: {sorter: 'archive_firstmatch'},
                        8: {sorter: 'paused'},
                        9: {sorter: 'subtitle'},
                        10: {sorter: 'default_ep_status'},
                        11: {sorter: 'status'},
                        12: {sorter: false},
                        13: {sorter: false},
                        14: {sorter: false},
                        15: {sorter: false},
                        16: {sorter: false},
                        17: {sorter: false}
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

                    window.location.href = 'massEdit?toEdit=' + checkArr.join('|');
                });

                $('#submitMassUpdate').on('click', function () {
                    var checkArr = [];

                    $('.showCheck:checked').each(function () {
                        checkArr.push($(this).attr('id'));
                    });

                    if (checkArr.length === 0) {
                        return;
                    }

                    window.location.href = 'massUpdate?toUpdate=' + checkArr.join('|');
                });

                $('#submitMassRescan').on('click', function () {
                    var checkArr = [];

                    $('.showCheck:checked').each(function () {
                        checkArr.push($(this).attr('id'));
                    });

                    if (checkArr.length === 0) {
                        return;
                    }

                    window.location.href = 'massUpdate?toRefresh=' + checkArr.join('|');
                });

                $('#submitMassRename').on('click', function () {
                    var checkArr = [];

                    $('.showCheck:checked').each(function () {
                        checkArr.push($(this).attr('id'));
                    });

                    if (checkArr.length === 0) {
                        return;
                    }

                    window.location.href = 'massUpdate?toRename=' + checkArr.join('|');
                });

                $('#submitMassDelete').on('click', function () {
                    var checkArr = [];

                    $('.showCheck:checked').each(function () {
                        checkArr.push($(this).attr('id'));
                    });

                    if (checkArr.length === 0) {
                        return;
                    }

                    $.bootbox.confirm("You have selected to delete " + checkArr.length + " show(s).  Are you sure you wish to continue? All files will be removed from your system.", function (result) {
                        if (result) {
                            window.location.href = 'massUpdate?toDelete=' + checkArr.join('|');
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

                    window.location.href = 'massUpdate?toRemove=' + checkArr.join('|');
                });

                $('.bulkCheck').on('click', function () {
                    $('.showCheck').each(function () {
                        if (!$(this).disabled) {
                            $(this).prop("checked", !this.checked);
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
                        $('#display_new_root_dir_' + curIndex).html('<b>DELETED</b>');
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
                    widgets: ['zebra'],
                    sortList: [[0, 0]],
                    headers: {3: {sorter: false}}
                });

                $('#limit').change(function () {
                    window.location.href = '/manage/failedDownloads/?limit=' + $(this).val();
                });

                $('#submitMassRemove').on('click', function () {
                    var removeArr = [];

                    $('.removeCheck').each(function () {
                        if ($(this).prop('checked')) {
                            removeArr.push($(this).attr('id').split('-')[1]);
                        }
                    });

                    if (removeArr.length === 0) {
                        return false;
                    }

                    window.location.href = '/manage/failedDownloads?toRemove=' + removeArr.join('|');
                });

                $('.bulkCheck').on('click', function () {
                    var bulkCheck = this;
                    var whichBulkCheck = $(bulkCheck).attr('id');

                    $('.' + whichBulkCheck + ':visible').each(function () {
                        $(this).prop("checked", bulkCheck.checked);
                    });
                });

                $('.removeCheck').forEach(function (name) {
                    var lastCheck = null;
                    $(name).click(function (event) {
                        if (!lastCheck || !event.shiftKey) {
                            lastCheck = this;
                            return;
                        }

                        var check = this;
                        var found = 0;

                        $(name + ':visible').each(function () {
                            switch (found) {
                                case 2:
                                    return false;
                                case 1:
                                    $(this).prop("checked", lastCheck.checked);
                            }

                            if (this === check || this === lastCheck) {
                                found++;
                            }
                        });
                    });
                });
            },

            subtitles_missed: function () {
                function makeRow(indexerId, season, episode, name, subtitles, checked) {
                    checked = checked ? ' checked' : '';

                    var row = '';
                    row += ' <tr class="good show-' + indexerId + '">';
                    row += '  <td align="center"><input type="checkbox" class="' + indexerId + '-epcheck" name="' + indexerId + '-' + season + 'x' + episode + '"' + checked + '></td>';
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
                        $.getJSON('/manage/showSubtitleMissed', {
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
            },
        },

        logs: {
            init: function () {
            },

            view: function () {
                $('#minLevel,#logFilter,#logSearch').on('keyup change', _.debounce(function () {
                    if ($('#logSearch').val().length > 0) {
                        $('#logFilter option[value="<NONE>"]').prop('selected', true);
                        $('#minLevel option[value=5]').prop('selected', true);
                    }
                    $('#minLevel').prop('disabled', true);
                    $('#logFilter').prop('disabled', true);
                    document.body.style.cursor = 'wait';
                    var url = '/logs/viewlog/?minLevel=' + $('select[name=minLevel]').val() + '&logFilter=' + $('select[name=logFilter]').val() + '&logSearch=' + $('#logSearch').val();
                    $.get(url, function (data) {
                        history.pushState('data', '', url);
                        $('pre').html($(data).find('pre').html());
                        $('#minLevel').prop('disabled', false);
                        $('#logFilter').prop('disabled', false);
                        document.body.style.cursor = 'default';
                    });
                }, 500));
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
