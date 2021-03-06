import users from '../fixtures/user.json'
import govDepartments from '../fixtures/govDepartment.json'

const user = users[0].fields
const govDepartment = govDepartments[0].fields

describe('The Home Page', () => {
  it('successfully loads', () => {
    cy.visit(Cypress.config('baseUrl'))
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
  it('displays the correct text', () => {
    cy.get('h1').contains(
      `Update supply chain information`
    )
    cy.get('h2').contains('Complete your monthly update')
    cy.get('li').contains('You need to complete your monthly update for 5 supply chains')
    cy.get('li').contains(
      'Select a supply chain to provide your regular monthly update or to update wider details.'
    )
  })
  it('displays correct table headers', () => {
    cy.get('thead').find('th').should('have.length', 3)
    cy.get('th').contains('Supply chain')
    cy.get('th').contains('No. strategic actions')
    cy.get('th').contains('Last updated')
  })
  it('displays 5 supply chains in the table', () => {
    cy.get('tbody').find('tr').should('have.length', 5)
  })
  it('displays correct items in pagination list', () => {
    cy.get('.moj-pagination__list').find('li').should('have.length', 3)
    cy.get('.moj-pagination__item--active').contains('1')
    cy.get('.moj-pagination__item').contains('2')
    cy.get('.moj-pagination__item').contains('Next')
  })
  it('displays second page of supply chains after clicking Next', () => {
    cy.contains('Next').click()
    cy.url().should('eq', Cypress.config('baseUrl') + '/?page=2')
    cy.get('tbody').find('tr').should('have.length', 1)
  })
  it('displays first page of supply chains after clicking Previous', () => {
    cy.contains('Previous').click()
    cy.url().should('eq', Cypress.config('baseUrl') + '/?page=1')
  })
})
