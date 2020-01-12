# parse-data-uri
parse a data uri into mime type and buffer

## usage
```js
var parseDataUri = require('parse-data-uri')

var dataUri = 'data:image/jpeg;base64,23423423...'

var parsed = parseDataUri(dataUri)

console.log(parsed)
// {
//   mimeType: 'image/jpeg',
//   data: Buffer < 00 00 00 ... > 
// }

```


## api
###`parseDataUri : ( dataUri: String ) => {mimeType: String, data: Buffer}`

## installation

    $ npm install parse-data-uri


## running the tests

From package root:

    $ npm install
    $ npm test


Special thanks to @tootallnate for writing [data-uri-to-buffer](https://npm.im/data-uri-to-buffer)

## contributors

- jden <jason@denizac.org>


## license

ISC. (c) MMXIV jden <jason@denizac.org>. See LICENSE.md
