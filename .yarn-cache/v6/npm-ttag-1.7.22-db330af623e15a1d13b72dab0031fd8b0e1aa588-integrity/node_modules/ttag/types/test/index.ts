import {
    addLocale,
    c,
    gettext,
    Headers,
    jt,
    LocaleData,
    msgid,
    ngettext,
    setDedent,
    setDefaultLang,
    t,
    Translations,
    useLocale,
    useLocales,
} from 'index';

const n = 10;

// $ExpectType StringWithRawData
const zero_or_one = msgid`${n} banana`;

// $ExpectType string
ngettext(zero_or_one, msgid`${n} bananas`, n);

// $ExpectType string
t`This is a test`;

// $ExpectType string | string[]
jt`This is a test`;

// $ExpectType void
setDefaultLang('en-us');

// $ExpectType BindedFunctions
c('context');

// $ExpectType string
c('context').t`This is inside a contex`;

// $ExpectType { 'content-type': string; 'plural-forms': string; }
const localeHeaders: Headers = {
    'content-type': 'a-content-type',
    'plural-forms': 'plural-form-string'
};

// $ExpectType { 'Any key to translate': string; }
const translations: Translations = {
    'Any key to translate': 'Qualquer chave para traduzir',
};

// $ExpectType { headers: Headers; translations: Translations; }
const localeData: LocaleData = {
    headers: localeHeaders,
    translations
};
// $ExpectType void
addLocale('pt-BR', localeData);

// $ExpectType string
gettext('Something');

// $ExpectType void
useLocale('nl_NL');

// $ExpectType void
setDedent(true);

// $ExpectError
setDedent(1);

// $ExpectType void
useLocales(['nl_NL', 'nl_BE']);

// $ExpectError
useLocales('es_AR');
