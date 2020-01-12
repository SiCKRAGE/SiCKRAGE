/**
 * Simple AJAX handling module.
 * tokenfield 0.9.10 <https://github.com/KaneCohen/tokenfield>
 * Copyright 2018 Kane Cohen <https://github.com/KaneCohen>
 * Available under BSD-3-Clause license
 */
export default function ajax(params, options = {}, callback = null) {
  let xhr = new XMLHttpRequest();
  let url = options.url;
  let paramsArr = [];
  for (let key in params) {
    paramsArr.push(`${key}=${params[key]}`);
  }

  let paramsString = paramsArr.join('&');

  if (options.type.toLowerCase() === 'get') {
    url += '?' + paramsString;
  }

  xhr.open(options.type, url, true);

  for (let header in options.headers) {
    let value = options.headers[header];
    if (typeof value === 'function') {
      value = value(params, options);
    }
    xhr.setRequestHeader(header, value);
  }

  if (callback) {
    xhr.onreadystatechange = callback;
  }

  xhr.send(params);

  return xhr;
}
