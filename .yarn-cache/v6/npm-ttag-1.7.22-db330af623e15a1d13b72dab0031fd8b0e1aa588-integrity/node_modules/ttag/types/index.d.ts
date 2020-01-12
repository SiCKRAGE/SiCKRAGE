// TypeScript Version: 2.3
export class StringWithRawData extends String {
    _strs: string[];
    _exprs: any[];
}

export interface Headers {
    'content-type'?: string;
    'plural-forms'?: string;
}

export interface Translations {
    [key: string]: any;
}

export interface LocaleData {
    headers: Headers;
    translations: Translations;
}

export function t(strings: TemplateStringsArray, ...expr: any[]): string;
export function jt(strings: TemplateStringsArray, ...expr: any[]): string | string[];
export function msgid(strings: TemplateStringsArray, ...expr: any[]): StringWithRawData;
export function gettext(id: string): string;
export function ngettext(...args: Array<(StringWithRawData|string|number)>): string;
export function addLocale(locale: string, data: LocaleData): void;
export function useLocale(locale: string): void;
export function setDedent(value: boolean): void;
export function setDefaultLang(lang: string): void;
export function useLocales(locales: string[]): void;

export interface BindedFunctions {
    t(strings: TemplateStringsArray, ...expr: any[]): string;
    jt(strings: TemplateStringsArray, ...expr: any[]): string | string[];
    gettext(id: string): string;
    ngettext(...args: Array<(StringWithRawData|string|number)>): string;
}

export function c(context: string): BindedFunctions;
