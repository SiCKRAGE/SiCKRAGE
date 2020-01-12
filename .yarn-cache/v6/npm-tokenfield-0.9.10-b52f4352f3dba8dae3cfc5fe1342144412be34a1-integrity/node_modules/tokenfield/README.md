# Tokenfield

Input field with tagging/token/chip capabilities written in raw JavaScript. Tokens in OS X or Chips in Android -  
small UI elements which are inserted into various input fields that often combine with autocomplete functionality.

Tokens allow designers to display extra information about input. For example, in email applications when typing an  
email address of the recipient, input field could display full name of the owner of a given email and a his/her picture.

This Tokenfield implementation is written in raw JavaScript without any extra dependencies like jQuery. it has one  
somewhat opinionated behavior - Tokenfield intended use case is work with structured data. More specifically, it expects  
autocomplete data to be JSOn formatted array of objects where each object contains token ID and token Name. More on that  
below.

## Examples

View live [examples here](https://kanecohen.github.io/tokenfield).

![GIF demo](https://cloud.githubusercontent.com/assets/578455/13090371/72c292d4-d506-11e5-914e-06fd19b21f11.gif)

## Usage

### Via JavaScript

Tokenfield could be applied to any visible `<input />` element that allows users  
to input text or number.

````js
// Given that we have following HTML element: <input class="my-input" />
var tf = new Tokenfield({
  el: document.querySelector('.my-input')
});
````

This action would create Tokenfield wrapped around given input element. Without additional options, this Tokenfield  
would allow users to add multiple token items without any specific restrictions. Only unique items are allowed, though,  
so it is not possible to add multiple items such as: "foo", "bar", "foo". Only first "foo" would be added and the last  
one discarded.


### Data

As it was mentioned above - Tokenfield is intended to be used with structured data - array of objects. With default  
options it expects that data returned by the autocomplete or filtered from a given set of items would look like that:  
````js
[{id: 1, name: 'Red'}, {id: 2, name: 'Blue'}, {id: 3, name: 'Greed'}, ... ]
````
You can see that each object has two properties - `id` and a `name`. With this format when you submit form where  
Tokenfield is located, server would receive not an array of string, but an array of IDs.  

However, that is a case only with tokens that are added via autocomplete. If Tokenfield accepts new tokens, then form  
would send an additional array which would contain an array of strings.

## Options

| Name | Type | Default | Description |
| ---- | ---- | ------- | ----------- |
| el | string or DOM node | null | DOM element or string with selector pointing at an element you want to turn into tokenfield. |
| form | bool, string or DOM node | true | Listens to reset event on the specified form. If set to `true` listens to immediate parent form. |
| items | array | [] | Array of objects amongst which autocomplete will try to find a match. Default format might look like this: `[{id: 1, name: 'foo'}, {id: 2, name: 'bar'}]` |
| setItems | array | [] | Array of objects which would be displayed as selected after Tokenfield has been created. |
| newItems | bool | true | Option to allow user to add custom tokens instead of using preset list of tokens or tokens retrieved from the server. |
| multiple | bool | true | Option to allow multiple tokens in the field. |
| maxItems | integer | 0 | Option to limit number of items. Set to 0 to remove the limit. |
| matchRegex | string | `'{value}'` | Regex string that would be used for matching - when regex is compiled {value} would be replaced with escaped user input. |
| matchFlags | string | `'i'` | Regex flags used in matching. Default is `i` - case insensitive matching. |
| matchStart | bool | `false` | Option to do matching only from the beginning of the string - it compiles match regex to basicall this format: `/^{value}/i`. |
| matchEnd | bool | `false` | Option to do matching only from the end of the string - it compiles match regex to basicall this format: `/{value}$/i`. |
| remote | object | | Details on that - below in Autocomplete section. |
| addItemOnBlur | bool | `false` | If set to true, will add new item to the tokenfield on input blur. Either sets new item or first match from suggested list. |
| delimiters | array | [] | Option to specify certain characters/sets of characters to be used as delimiters during tokenization or input events on tokenfield. |
| addItemsOnPaste | bool | `false` | If set to true, will add new item to the tokenfield on paste. Tokenization happens using delimiters options listed above. |
| placeholder | null or string | null | Set a placeholder that will be shown in the input. If set to null, will try to use placeholder attribute from the original element set in `el` |
| inputType | string | `'text'` | Specifies HTML `type` attribute for the input element. |
| minChars | integer | 2 | Specifies how many characters user has to input before autocomplete suggester is shown. |
| maxSuggest | integer | 10 | Specifies how many suggestions should be shown. |
| itemLabel | string | `'name'` | Property of an item object which is used to display text in tokens. |
| itemName | string | `'items'` | Each token item will have its own hidden input which will contain an ID of a given item and a name attribute in an array format. This option sets a name. By default it is set to "items" which means that when user will submit a form server would receive an array of IDs under the name "items". |
| newItemName | string | `'items_new'` | Same as the above except it is only related to new items which were not added via autocomplete. |
| itemValue | string | `'id'` | Specifies which property from the autocomplete data to use as a primary identifying value. |
| itemData | string | `'name'` | Which property should be used when you do autocomplete on a given array of items. |

### Remote Options

Below you will find list of options which are related to remote autocomplete requests. Options are set as properties  
of an object assigned to `remote` property of the parent options object:

````js
new Tokenfield({
  remote: {
    url: "http://example.com",
    ...
  }
});
````

| Name | Type | Default | Description |
| ---- | ---- | ------- | ----------- |
| type | string | `'GET'` | Sets AJAX request type. Usually GET or POST |
| url | string | null | Specifies which URL will be used to retrieve autocomplete data. If set to null - remote autocomplete won't be performed. |
| queryParam | string | `'q'` | Sets name of the parameter which would contain value that user typed in the input field. |
| delay | integer | 300 | Sets delay in milliseconds after which remote request is performed. |
| timestampParam | string | `'t'` | Sets parameter for the timestamp when remote call was requested. |
| params | object | `{}` | Sets any additional AJAX params |
| headers | object | `{}` | Sets AJAX headers. Could be simple key:value items, or key:function items if you want to add headers dynamically |

## Events

Tokenfield uses standard node.js EventEmitter and therefore supports such
event as: 'on', 'once', 'removeAllListeners', 'removeListener'.

For more details on EventEmitter, please check official [documentation page](https://nodejs.org/api/events.html).

Available events are:

| Event Type | Description |
| ---------- | ----------- |
| change | Fired after any change in tokens list - after adding or removing tokens, setting multiple tokens manually etc. |
| showSuggestions | Fired before Tokenfield would show suggestions box. |
| shownSuggestions | Fired after Tokenfield has shown suggestions box. |
| hideSuggestions | Fired before Tokenfield would hide suggestions box. |
| hiddenSuggestions | Fired after Tokenfield has hidden suggestions box. |
| addToken | Fired before token has been added to the tokenfield. Second argument contains token data. |
| addedToken | Fired after token has been added to internal token list. |
| removeToken | Fired before token has been removed from the tokenfield. Second argument contains token data. |
| removedToken | Fired after token has been removed from the tokenfield. Second argument contains removed token data. |

## Helper Methods

Tokenfield has several overridable methods which allow user to remap given token data or change how some elements are  
rendered.

Available methods are:

| Method name | Description |
| ---------- | ----------- |
| remapData | Fired on every data request. Override it if you want to change structure of an available data - change props names, sanitize property values, remove props. Just make sure to return array of objects which would be consumed by the tokenfield instance. |
| renderSetItemLabel | Fired on token item render. Override this method in order to change how label for each token is rendered |
| onInput | Fired when you type something in the input field. Accepts value of the input field and event object. |
