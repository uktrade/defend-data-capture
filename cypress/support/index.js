import 'cypress-axe'
import './utils'
import './commands'

const logA11yIssues = violations => {
  const violationData = violations.map(({ impact, help, nodes }) => ({
    impact,
    help,
    html: nodes[0].html,
  }))

  const docsLinks = violations.map(({ helpUrl }) => ({
    linkToDocs: helpUrl,
  }))

  cy.task('table', violationData)
  cy.task('table', docsLinks)
}

Cypress.Commands.add('runA11y', (context = null, options = null) => {
  cy.checkA11y(context, options, logA11yIssues)
})


Cypress.Cookies.defaults({
  preserve: ['sessionid', 'csrftoken']
})
