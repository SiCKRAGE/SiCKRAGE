/*eslint-disable*/

const SENTRY_LOADER_RE = /sentry\.loader\.js$/;
const SENTRY_MODULE_RE = /sentry-webpack\.module\.js$/;

const mockCli = {
  releases: {
    new: jest.fn(() => Promise.resolve()),
    uploadSourceMaps: jest.fn(() => Promise.resolve()),
    finalize: jest.fn(() => Promise.resolve()),
    proposeVersion: jest.fn(() => Promise.resolve()),
    setCommits: jest.fn(() => Promise.resolve()),
  },
};

const SentryCliMock = jest.fn((configFile, options) => mockCli);
const SentryCli = jest.mock('@sentry/cli', () => SentryCliMock);
const SentryCliPlugin = require('..');

afterEach(() => {
  jest.clearAllMocks();
});

describe('constructor', () => {
  test('uses defaults without options', () => {
    const sentryCliPlugin = new SentryCliPlugin();

    expect(sentryCliPlugin.options).toEqual({
      rewrite: true,
    });
  });

  test('merges defaults with options', () => {
    const sentryCliPlugin = new SentryCliPlugin({
      foo: 42,
    });

    expect(sentryCliPlugin.options).toEqual({
      rewrite: true,
      foo: 42,
    });
  });

  test('uses declared options over defaults', () => {
    const sentryCliPlugin = new SentryCliPlugin({
      rewrite: false,
    });

    expect(sentryCliPlugin.options).toEqual({
      rewrite: false,
    });
  });

  test('allows to provide debug mode', () => {
    let sentryCliPlugin = new SentryCliPlugin();
    expect(sentryCliPlugin.debug).toEqual(false);

    sentryCliPlugin = new SentryCliPlugin({
      debug: true,
    });
    expect(sentryCliPlugin.debug).toEqual(true);
  });

  test('sanitizes array options `include` and `ignore`', () => {
    const sentryCliPlugin = new SentryCliPlugin({
      include: 'foo',
      ignore: 'bar',
    });

    expect(sentryCliPlugin.options).toEqual({
      rewrite: true,
      include: ['foo'],
      ignore: ['bar'],
    });
  });

  test('keeps array options `include` and `ignore`', () => {
    const sentryCliPlugin = new SentryCliPlugin({
      include: ['foo'],
      ignore: ['bar'],
    });

    expect(sentryCliPlugin.options).toEqual({
      rewrite: true,
      include: ['foo'],
      ignore: ['bar'],
    });
  });
});

describe('CLI configuration', () => {
  test('passes the configuration file to CLI', () => {
    const sentryCliPlugin = new SentryCliPlugin({
      configFile: 'some/sentry.properties',
    });

    expect(SentryCliMock).toHaveBeenCalledWith('some/sentry.properties', {
      silent: false,
    });
  });

  test('only creates a single CLI instance', () => {
    const sentryCliPlugin = new SentryCliPlugin({});
    sentryCliPlugin.apply({ hooks: { afterEmit: { tapAsync: jest.fn() } } });
    expect(SentryCliMock.mock.instances.length).toBe(1);
  });
});

describe('afterEmitHook', () => {
  let compiler;
  let compilation;
  let compilationDoneCallback;

  beforeEach(() => {
    compiler = {
      hooks: {
        afterEmit: {
          tapAsync: jest.fn((name, callback) =>
            callback(compilation, compilationDoneCallback)
          ),
        },
      },
    };

    compilation = { errors: [], hash: 'someHash' };
    compilationDoneCallback = jest.fn();
  });

  test('calls `hooks.afterEmit.tapAsync()`', () => {
    const sentryCliPlugin = new SentryCliPlugin();
    sentryCliPlugin.apply(compiler);

    expect(compiler.hooks.afterEmit.tapAsync).toHaveBeenCalledWith(
      'SentryCliPlugin',
      expect.any(Function)
    );
  });

  test('calls `compiler.plugin("after-emit")` legacy Webpack <= 3', () => {
    const sentryCliPlugin = new SentryCliPlugin();

    // Simulate Webpack <= 2
    compiler = { plugin: jest.fn() };
    sentryCliPlugin.apply(compiler);

    expect(compiler.plugin).toHaveBeenCalledWith(
      'after-emit',
      expect.any(Function)
    );
  });

  test('errors without `include` option', done => {
    const sentryCliPlugin = new SentryCliPlugin({ release: 42 });
    sentryCliPlugin.apply(compiler);

    setImmediate(() => {
      expect(compilationDoneCallback).toBeCalled();
      expect(compilation.errors).toEqual([
        'Sentry CLI Plugin: `include` option is required',
      ]);
      done();
    });
  });

  test('creates a release on Sentry', done => {
    expect.assertions(4);

    const sentryCliPlugin = new SentryCliPlugin({
      include: 'src',
      release: 42,
    });
    sentryCliPlugin.apply(compiler);

    setImmediate(() => {
      expect(mockCli.releases.new).toBeCalledWith('42');
      expect(mockCli.releases.uploadSourceMaps).toBeCalledWith('42', {
        ignore: undefined,
        release: 42,
        include: ['src'],
        rewrite: true,
      });
      expect(mockCli.releases.finalize).toBeCalledWith('42');
      expect(compilationDoneCallback).toBeCalled();
      done();
    });
  });

  test('handles errors during releasing', done => {
    expect.assertions(2);
    mockCli.releases.new.mockImplementationOnce(() =>
      Promise.reject(new Error('Pickle Rick'))
    );

    const sentryCliPlugin = new SentryCliPlugin({
      include: 'src',
      release: 42,
    });
    sentryCliPlugin.apply(compiler);

    setImmediate(() => {
      expect(compilation.errors).toEqual(['Sentry CLI Plugin: Pickle Rick']);
      expect(compilationDoneCallback).toBeCalled();
      done();
    });
  });

  test('handles errors with errorHandler option', done => {
    expect.assertions(3);
    mockCli.releases.new.mockImplementationOnce(() =>
      Promise.reject(new Error('Pickle Rick'))
    );
    let e;

    const sentryCliPlugin = new SentryCliPlugin({
      include: 'src',
      release: 42,
      errorHandler: err => {
        e = err;
      },
    });
    sentryCliPlugin.apply(compiler);

    setImmediate(() => {
      expect(compilation.errors).toEqual([]);
      expect(e.message).toEqual('Pickle Rick');
      expect(compilationDoneCallback).toBeCalled();
      done();
    });
  });

  test('test setCommits with flat options', done => {
    const sentryCliPlugin = new SentryCliPlugin({
      include: 'src',
      release: '42',
      commit: '4d8656426ca13eab19581499da93408e30fdd9ef',
      previousCommit: 'b6b0e11e74fd55836d3299cef88531b2a34c2514',
      repo: 'group / repo',
      auto: false,
    });

    sentryCliPlugin.apply(compiler);

    setImmediate(() => {
      expect(mockCli.releases.setCommits).toBeCalledWith('42', {
        repo: 'group / repo',
        commit: '4d8656426ca13eab19581499da93408e30fdd9ef',
        previousCommit: 'b6b0e11e74fd55836d3299cef88531b2a34c2514',
        auto: false,
      });
      expect(compilationDoneCallback).toBeCalled();
      done();
    });
  });

  test('test setCommits with grouped options', done => {
    const sentryCliPlugin = new SentryCliPlugin({
      include: 'src',
      release: '42',
      setCommits: {
        commit: '4d8656426ca13eab19581499da93408e30fdd9ef',
        previousCommit: 'b6b0e11e74fd55836d3299cef88531b2a34c2514',
        repo: 'group / repo',
        auto: false,
      },
    });

    sentryCliPlugin.apply(compiler);

    setImmediate(() => {
      expect(mockCli.releases.setCommits).toBeCalledWith('42', {
        repo: 'group / repo',
        commit: '4d8656426ca13eab19581499da93408e30fdd9ef',
        previousCommit: 'b6b0e11e74fd55836d3299cef88531b2a34c2514',
        auto: false,
      });
      expect(compilationDoneCallback).toBeCalled();
      done();
    });
  });
});

describe('module rule overrides', () => {
  let compiler;
  let sentryCliPlugin;

  beforeEach(() => {
    sentryCliPlugin = new SentryCliPlugin({ release: '42', include: 'src' });
    compiler = {
      hooks: { afterEmit: { tapAsync: jest.fn() } },
      options: { module: {} },
    };
  });

  test('injects a `rule` for our mock module', done => {
    expect.assertions(1);

    compiler.options.module.rules = [];
    sentryCliPlugin.apply(compiler);

    setImmediate(() => {
      expect(compiler.options.module.rules[0]).toEqual({
        test: /sentry-webpack\.module\.js$/,
        use: [
          {
            loader: expect.stringMatching(SENTRY_LOADER_RE),
            options: { releasePromise: expect.any(Promise) },
          },
        ],
      });
      done();
    });
  });

  test('injects a `loader` for our mock module', done => {
    expect.assertions(1);

    compiler.options.module.loaders = [];
    sentryCliPlugin.apply(compiler);

    setImmediate(() => {
      expect(compiler.options.module.loaders[0]).toEqual({
        test: /sentry-webpack\.module\.js$/,
        loader: expect.stringMatching(SENTRY_LOADER_RE),
        options: { releasePromise: expect.any(Promise) },
      });
      done();
    });
  });

  test('defaults to `rules` when nothing is specified', done => {
    expect.assertions(1);
    sentryCliPlugin.apply(compiler);

    setImmediate(() => {
      expect(compiler.options.module.rules).toBeInstanceOf(Array);
      done();
    });
  });

  test('creates the `module` option if missing', done => {
    expect.assertions(1);

    delete compiler.options.module;
    sentryCliPlugin.apply(compiler);

    setImmediate(() => {
      expect(compiler.options.module).not.toBeUndefined();
      done();
    });
  });
});

describe('entry point overrides', () => {
  let compiler;
  let sentryCliPlugin;

  beforeEach(() => {
    sentryCliPlugin = new SentryCliPlugin({ release: '42', include: 'src' });
    compiler = {
      hooks: { afterEmit: { tapAsync: jest.fn() } },
      options: { module: { rules: [] } },
    };
  });

  test('creates an entry if none is specified', done => {
    expect.assertions(1);
    sentryCliPlugin.apply(compiler);

    setImmediate(() => {
      expect(compiler.options.entry).toMatch(SENTRY_MODULE_RE);
      done();
    });
  });

  test('injects into a single entry', done => {
    expect.assertions(1);

    compiler.options.entry = './src/index.js';
    sentryCliPlugin.apply(compiler);

    setImmediate(() => {
      expect(compiler.options.entry).toEqual([
        expect.stringMatching(SENTRY_MODULE_RE),
        './src/index.js',
      ]);
      done();
    });
  });

  test('injects into an array entry', done => {
    expect.assertions(1);

    compiler.options.entry = ['./src/preload.js', './src/index.js'];
    sentryCliPlugin.apply(compiler);

    setImmediate(() => {
      expect(compiler.options.entry).toEqual([
        expect.stringMatching(SENTRY_MODULE_RE),
        './src/preload.js',
        './src/index.js',
      ]);
      done();
    });
  });

  test('injects into multiple entries', done => {
    expect.assertions(1);

    compiler.options.entry = {
      main: './src/index.js',
      admin: './src/admin.js',
    };
    sentryCliPlugin.apply(compiler);

    setImmediate(() => {
      expect(compiler.options.entry).toEqual({
        main: [expect.stringMatching(SENTRY_MODULE_RE), './src/index.js'],
        admin: [expect.stringMatching(SENTRY_MODULE_RE), './src/admin.js'],
      });
      done();
    });
  });

  test('injects into multiple entries with array chunks', done => {
    expect.assertions(1);

    compiler.options.entry = {
      main: ['./src/index.js', './src/common.js'],
      admin: ['./src/admin.js', './src/common.js'],
    };
    sentryCliPlugin.apply(compiler);

    setImmediate(() => {
      expect(compiler.options.entry).toEqual({
        main: [
          expect.stringMatching(SENTRY_MODULE_RE),
          './src/index.js',
          './src/common.js',
        ],
        admin: [
          expect.stringMatching(SENTRY_MODULE_RE),
          './src/admin.js',
          './src/common.js',
        ],
      });
      done();
    });
  });

  test('injects into entries specified by a function', done => {
    expect.assertions(1);

    compiler.options.entry = () => Promise.resolve('./src/index.js');
    sentryCliPlugin.apply(compiler);

    setImmediate(() => {
      compiler.options.entry().then(entry => {
        expect(entry).toEqual([
          expect.stringMatching(SENTRY_MODULE_RE),
          './src/index.js',
        ]);
        done();
      });
    });
  });

  test('filters entry points by name', done => {
    expect.assertions(1);

    compiler.options.entry = {
      main: './src/index.js',
      admin: './src/admin.js',
    };
    sentryCliPlugin.options.entries = ['admin'];
    sentryCliPlugin.apply(compiler);

    setImmediate(() => {
      expect(compiler.options.entry).toEqual({
        main: './src/index.js',
        admin: [expect.stringMatching(SENTRY_MODULE_RE), './src/admin.js'],
      });
      done();
    });
  });

  test('filters entry points by RegExp', done => {
    expect.assertions(1);

    compiler.options.entry = {
      main: './src/index.js',
      admin: ['./src/admin.js', './src/common.js'],
    };
    sentryCliPlugin.options.entries = /^ad/;
    sentryCliPlugin.apply(compiler);

    setImmediate(() => {
      expect(compiler.options.entry).toEqual({
        main: './src/index.js',
        admin: [
          expect.stringMatching(SENTRY_MODULE_RE),
          './src/admin.js',
          './src/common.js',
        ],
      });
      done();
    });
  });

  test('filters entry points by function', done => {
    expect.assertions(1);

    compiler.options.entry = {
      main: ['./src/index.js', './src/common.js'],
      admin: './src/admin.js',
    };
    sentryCliPlugin.options.entries = key => key == 'admin';
    sentryCliPlugin.apply(compiler);

    setImmediate(() => {
      expect(compiler.options.entry).toEqual({
        main: ['./src/index.js', './src/common.js'],
        admin: [expect.stringMatching(SENTRY_MODULE_RE), './src/admin.js'],
      });
      done();
    });
  });

  test('throws for an invalid `entries` option', () => {
    compiler.options.entry = {
      main: './src/index.js',
      admin: './src/admin.js',
    };
    sentryCliPlugin.options.entries = 42;
    expect(() => sentryCliPlugin.apply(compiler)).toThrowError(/entries/);
  });
});
