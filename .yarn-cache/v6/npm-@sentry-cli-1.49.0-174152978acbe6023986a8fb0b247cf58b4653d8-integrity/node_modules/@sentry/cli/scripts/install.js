#!/usr/bin/env node

'use strict';

const fs = require('fs');
const http = require('http');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const zlib = require('zlib');
const stream = require('stream');

const HttpsProxyAgent = require('https-proxy-agent');
const fetch = require('node-fetch');
const ProgressBar = require('progress');
const Proxy = require('proxy-from-env');
const copyFileSync = require('fs-copy-file-sync');
const mkdirp = require('mkdirp');

const helper = require('../js/helper');
const pkgInfo = require('../package.json');

const CDN_URL =
  process.env.SENTRYCLI_LOCAL_CDNURL ||
  process.env.npm_config_sentrycli_cdnurl ||
  process.env.SENTRYCLI_CDNURL ||
  'https://downloads.sentry-cdn.com/sentry-cli';

function getDownloadUrl(platform, arch) {
  const releasesUrl = `${CDN_URL}/${pkgInfo.version}/sentry-cli`;
  const archString = arch.indexOf('64') > -1 ? 'x86_64' : 'i686';
  switch (platform) {
    case 'darwin':
      return `${releasesUrl}-Darwin-x86_64`;
    case 'win32':
      return `${releasesUrl}-Windows-${archString}.exe`;
    case 'linux':
    case 'freebsd':
      return `${releasesUrl}-Linux-${archString}`;
    default:
      return null;
  }
}

function createProgressBar(name, total) {
  if (process.stdout.isTTY) {
    return new ProgressBar(`fetching ${name} :bar :percent :etas`, {
      complete: '█',
      incomplete: '░',
      width: 20,
      total,
    });
  }

  let pct = null;
  let current = 0;
  return {
    tick: length => {
      current += length;
      const next = Math.round((current / total) * 100);
      if (next > pct) {
        pct = next;
        process.stdout.write(`fetching ${name} ${pct}%\n`);
      }
    },
  };
}

function npmCache() {
  const env = process.env;
  return (
    env.npm_config_cache ||
    env.npm_config_yarn_offline_mirror ||
    (env.APPDATA ? path.join(env.APPDATA, 'npm-cache') : path.join(os.homedir(), '.npm'))
  );
}

function getCachedPath(url) {
  const digest = crypto
    .createHash('md5')
    .update(url)
    .digest('hex')
    .slice(0, 6);

  return path.join(
    npmCache(),
    'sentry-cli',
    `${digest}-${path.basename(url).replace(/[^a-zA-Z0-9.]+/g, '-')}`
  );
}

function getTempFile(cached) {
  return `${cached}.${process.pid}-${Math.random()
    .toString(16)
    .slice(2)}.tmp`;
}

function downloadBinary() {
  const arch = os.arch();
  const platform = os.platform();
  const outputPath = helper.getPath();

  const downloadUrl = getDownloadUrl(platform, arch);
  if (!downloadUrl) {
    return Promise.reject(new Error(`unsupported target ${platform}-${arch}`));
  }

  const cachedPath = getCachedPath(downloadUrl);
  if (fs.existsSync(cachedPath)) {
    copyFileSync(cachedPath, outputPath);
    return Promise.resolve();
  }

  const proxyUrl = Proxy.getProxyForUrl(downloadUrl);
  const agent = proxyUrl ? new HttpsProxyAgent(proxyUrl) : null;

  return fetch(downloadUrl, {
    agent,
    compress: false,
    headers: {
      'accept-encoding': 'gzip, deflate, br',
    },
    redirect: 'follow',
  }).then(response => {
    if (!response.ok) {
      throw new Error(`Received ${response.status}: ${response.statusText}`);
    }

    const contentEncoding = response.headers.get('content-encoding');
    let decompressor;
    if (/\bgzip\b/.test(contentEncoding)) {
      decompressor = zlib.createGunzip();
    } else if (/\bdeflate\b/.test(contentEncoding)) {
      decompressor = zlib.createInflate();
    } else if (/\bbr\b/.test(contentEncoding)) {
      decompressor = zlib.createBrotliDecompress();
    } else {
      decompressor = new stream.PassThrough();
    }
    const name = downloadUrl.match(/.*\/(.*?)$/)[1];
    const total = parseInt(response.headers.get('content-length'), 10);
    const progressBar = createProgressBar(name, total);
    const tempPath = getTempFile(cachedPath);
    mkdirp.sync(path.dirname(tempPath));

    return new Promise((resolve, reject) => {
      response.body
        .on('error', e => reject(e))
        .on('data', chunk => progressBar.tick(chunk.length))
        .pipe(decompressor)
        .pipe(fs.createWriteStream(tempPath, { mode: '0755' }))
        .on('error', e => reject(e))
        .on('close', () => resolve());
    }).then(() => {
      copyFileSync(tempPath, cachedPath);
      copyFileSync(tempPath, outputPath);
      fs.unlinkSync(tempPath);
    });
  });
}

function checkVersion() {
  return helper.execute(['--version']).then(output => {
    const version = output.replace('sentry-cli ', '').trim();
    const expected = process.env.SENTRYCLI_LOCAL_CDNURL ? 'DEV' : pkgInfo.version;
    if (version !== expected) {
      throw new Error(
        `Unexpected sentry-cli version "${version}", expected "${expected}"`
      );
    }
  });
}

if (process.env.SENTRYCLI_LOCAL_CDNURL) {
  // For testing, mock the CDN by spawning a local server
  const server = http.createServer((request, response) => {
    const contents = fs.readFileSync(path.join(__dirname, '../js/__mocks__/sentry-cli'));
    response.writeHead(200, {
      'Content-Type': 'application/octet-stream',
      'Content-Length': String(contents.byteLength),
    });
    response.end(contents);
  });

  server.listen(8999);
  process.on('exit', () => server.close());
}

downloadBinary()
  .then(() => checkVersion())
  .then(() => process.exit(0))
  .catch(e => {
    // eslint-disable-next-line no-console
    console.error(e.toString());
    process.exit(1);
  });
