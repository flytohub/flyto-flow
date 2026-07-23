import { describe, expect, it } from 'vitest'
import { mount, RouterLinkStub } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'

import AppNavbar from '@/components/layout/AppNavbar.vue'

function mountNavbar() {
  const i18n = createI18n({
    legacy: false,
    locale: 'en',
    messages: {
      en: {
        mcpStudio: {
          nav: 'MCP',
          primaryNavigation: 'Primary navigation',
          toggleNavigation: 'Toggle navigation',
        },
        observability: { title: 'Observability' },
        variables: { title: 'Variables' },
        workflow: { title: 'Workflows' },
      },
    },
  })

  return mount(AppNavbar, {
    global: {
      plugins: [i18n],
      stubs: {
        LanguageSwitcher: true,
        RouterLink: RouterLinkStub,
      },
    },
  })
}

describe('AppNavbar.vue', () => {
  it('keeps Flow routes inside the Cloud-aligned desktop navigation shell', () => {
    const wrapper = mountNavbar()
    const links = wrapper.findAllComponents(RouterLinkStub)
      .filter(link => link.props('to') !== '/')

    expect(links.map(link => link.props('to'))).toEqual([
      '/my-templates',
      '/mcp',
      '/variables',
      '/observability',
    ])
    expect(wrapper.text()).toContain('Workflows')
    expect(wrapper.text()).toContain('MCP')
    expect(wrapper.text()).toContain('Variables')
    expect(wrapper.text()).toContain('Observability')

    const navigation = wrapper.get('.app-navbar__desktop-navigation')
    expect(navigation.classes()).toContain('md:flex')
    expect(navigation.classes()).not.toContain('absolute')
  })

  it('opens the Cloud-aligned mobile navigation from its menu button', async () => {
    const wrapper = mountNavbar()

    await wrapper.get('.app-navbar__mobile-menu-button').trigger('click')

    expect(wrapper.findAll('.mobile-nav-link')).toHaveLength(4)
  })
})
