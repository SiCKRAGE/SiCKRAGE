import { expect } from 'chai';
import { XMLHttpRequest } from 'xmlhttprequest';
import ajax from '../lib/ajax.js';

global.XMLHttpRequest = XMLHttpRequest;

describe('ajax', () => {
  it('should create XHR instance', () => {
    let maybeXhr = ajax({
      q: 'Hello World'
    }, {
      type: 'GET',
      url: null,
      delay: 300,
      timestampParam: 't',
      params: {},
      headers: {}
    });

    expect(maybeXhr).to.be.an.instanceof(XMLHttpRequest);
  });

  it('should create XHR instance with headers', () => {
    let maybeXhr = ajax({
      q: 'Hello World'
    }, {
      type: 'GET',
      url: null,
      delay: 300,
      timestampParam: 't',
      params: {},
      headers: {'foo': 'bar', 'hello': () => 'world'}
    });

    expect(maybeXhr.getRequestHeader('foo')).to.equal('bar');
    expect(maybeXhr.getRequestHeader('hello')).to.equal('world');
  });
});
