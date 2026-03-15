import { createI18n } from 'vue-i18n';
import zh from '@/locales/zh';
import en from '@/locales/en';

export type MessageSchema = typeof en;

const i18n = createI18n<[MessageSchema], 'en' | 'zh'>({
  legacy: false,
  locale: localStorage.getItem('language') || 'zh',
  fallbackLocale: 'en',
  messages: {
    zh: zh as any,
    en: en as any
  }
});

export default i18n;

export function setI18nLanguage(locale: 'en' | 'zh'): void {
  (i18n.global as any).locale.value = locale;
  localStorage.setItem('language', locale);
  document.documentElement.setAttribute('lang', locale);
}

export function getI18nLanguage(): 'en' | 'zh' {
  return (i18n.global as any).locale.value as 'en' | 'zh';
}
