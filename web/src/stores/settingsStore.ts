import { defineStore } from 'pinia';
import { setI18nLanguage } from '@/i18n';

type Theme = 'light' | 'dark';
type Language = 'en' | 'zh';

export const useSettingsStore = defineStore('settings', {
  state: (): { language: Language; theme: Theme } => ({
    language: (localStorage.getItem('language') as Language) || 'en',
    theme: 'light'
  }),
  actions: {
    setLanguage(lang: Language): void {
      this.language = lang;
      setI18nLanguage(lang);
    },
    setTheme(nextTheme: Theme): void {
      this.theme = nextTheme;
    }
  }
});
