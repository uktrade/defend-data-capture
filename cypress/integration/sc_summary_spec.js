import govDepartments from '../fixtures/govDepartment.json'
import supplyChains from '../fixtures/supplyChains.json'
import users from '../fixtures/user.json'

const govDepartment = govDepartments[0].fields
const supplyChain = supplyChains[0]
const user = users[0].fields

describe('Supply chain summary page', () => {
  it('successfully loads', () => {
    cy.visit(Cypress.config('baseUrl') + `/${supplyChain.fields.slug}/summary`)
    cy.injectAxe()
  })
  it('has no accessibility issues', () => {
    cy.runA11y()
  })
  it("displays user's name and department in header", () => {
    cy.get('.app-header-item').should(
      'have.text',
      `${user.first_name} ${user.last_name} - ${govDepartment.name}`
    )
  })
  it('displays breadcrumbs', () => {
    cy.get('li').contains('Home').should('have.attr', 'href').and('eq', '/')
    cy.get('li')
      .contains(`${supplyChain.fields.name}`)
      .should('have.attr', 'href')
      .and('eq', `/${supplyChain.fields.slug}`)
    cy.get('li')
      .contains(`Full details of ${supplyChain.fields.name}`)
      .should('have.attr', 'href')
      .and('eq', `/${supplyChain.fields.slug}/summary`)
  })
  it('displays the header', () => {
    cy.get('h1').contains(`Summary of ${supplyChain.fields.name}`)
  })

  it('displays correct table values', () => {
    const table = cy
      .get('dl')
      .first()
      .children()

    table.should('have.length', 4)
    const tableElement = '.govuk-summary-list__row'

    cy.forms.checkSummaryTableContent(
      table,
      tableElement,
      0,
      'The contact for this supply chain',
      supplyChain.fields.contact_name
    )

    cy.forms.checkSummaryTableContent(
      table,
      tableElement,
      1,
      'The email for the supply chain contact',
      supplyChain.fields.contact_email
    )

    cy.forms.checkSummaryTableContent(
      table,
      tableElement,
      2,
      String.raw`The current vulnerability status is 'Low'. Is this accurate?`,
      'No' + ' ' + supplyChain.fields.vulnerability_status_disagree_reason
    )

    cy.forms.checkSummaryTableContent(
      table,
      tableElement,
      3,
      String.raw`The current risk severity level is 'Medium'. Is this accurate?`,
      'Yes'
    )
  })
  it('takes user to task list when button is clicked', () => {
    cy.get('a').contains('Back to task list').click()
    cy.url().should(
      'eq',
      Cypress.config('baseUrl') + `/${supplyChain.fields.slug}`
    )
  })
})
