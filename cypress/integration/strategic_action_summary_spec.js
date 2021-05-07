import govDepartments from '../fixtures/govDepartment.json'
import supplyChains from '../fixtures/supplyChains.json'
import users from '../fixtures/user.json'
import allActions from '../fixtures/strategicActions.json'

const govDepartment = govDepartments[0].fields
const supplyChain = supplyChains[5] // Uses Supply Chain 6 fixture
const user = users[0].fields
const actions = allActions
  .filter(action => action.fields.supply_chain === supplyChain.pk)
  .map(action => action.fields)

describe('The strategic action summary page', () => {
  it('successfully loads', () => {
    cy.visit(
      Cypress.config('baseUrl') +
        `/${supplyChain.fields.slug}/strategic-actions`
    )
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
      .contains(`Strategic actions for ${supplyChain.fields.name}`)
      .should('have.attr', 'href')
      .and('eq', `/${supplyChain.fields.slug}/strategic-actions`)
  })
  it('displays the header and paragraph text', () => {
    cy.get('h1').contains(`Strategic actions for ${supplyChain.fields.name}`)
    cy.get('p').contains(
      'Select a strategic action to view its details.'
    )
  })
  it('displays 5 accordian sections with a heading and summary', () => {
    const checkAccordionHeadingsandSummaries = (object, index) => {
      cy.get('.govuk-accordion__section')
        .eq(index)
        .within(() => {
          cy.get('.govuk-accordion__section-heading').contains(object.name)
          cy.get('.govuk-accordion__section-summary').contains(
            object.description
          )
        })
    }

    cy.get('.govuk-accordion__section').should('have.length', 5)
    cy.get('.govuk-accordion__section-summary').should('have.length', 5)
    checkAccordionHeadingsandSummaries(actions[0], 0)
    checkAccordionHeadingsandSummaries(actions[1], 1)
    checkAccordionHeadingsandSummaries(actions[2], 2)
    checkAccordionHeadingsandSummaries(actions[3], 3)
    checkAccordionHeadingsandSummaries(actions[4], 4)
  })

  it('opens all sections when open all is clicked', () => {
    cy.contains('Open all').click()
    cy.get('div > .govuk-accordion__section-content')
      .should('be.visible')
      .and('have.length', 5)
  })
  it('closes all sections when close all is clicked', () => {
    cy.contains('Close all').click()
    cy.get('div > .govuk-accordion__section-content').should('not.be.visible')
  })
  it('opens a section when the + symbol is clicked', () => {
    cy.get('.govuk-accordion__section-heading > button > span')
      .first()
      .click({ force: true })
    cy.get('div > .govuk-accordion__section-content').should('be.visible')
  })

  it('displays correct table values', () => {
    const firstTable = cy
      .get('.govuk-accordion__section-content > dl')
      .first()
      .children()

    firstTable.should('have.length', 8)
    const tableElement = '.govuk-summary-list__row'

    cy.forms.checkSummaryTableContent(
      firstTable,
      tableElement,
      0,
      'What does the strategic action involve?',
      actions[0].description
    )

    cy.forms.checkSummaryTableContent(
      firstTable,
      tableElement,
      1,
      'What is the intended impact of the strategic action? How will the action be measured?',
      actions[0].impact
    )

    cy.forms.checkSummaryTableContent(
      firstTable,
      tableElement,
      2,
      'Which category applies to this strategic action?',
      'Diversify'
    )

    cy.forms.checkSummaryTableContent(
      firstTable,
      tableElement,
      3,
      'Does the strategic action apply UK-wide or in England only?',
      'England only'
    )

    cy.forms.checkSummaryTableContent(
      firstTable,
      tableElement,
      4,
      'Which other government departments are supporting this strategic action?',
      'MoD'
    )

    cy.forms.checkSummaryTableContent(
      firstTable,
      tableElement,
      5,
      'What is the estimated date of completion?',
      '02/08/2023'
    )

    cy.forms.checkSummaryTableContent(
      firstTable,
      tableElement,
      6,
      'Are there any other dependencies or requirements for applying this strategic action?',
      actions[0].other_dependencies
    )

    cy.forms.checkSummaryTableContent(
      firstTable,
      tableElement,
      7,
      'Does this action affect the whole supply chain or a section of supply chains?',
      actions[0].specific_related_products
    )
  })
  it('closes a section with the - symbol is clicked', () => {
    cy.get('.govuk-accordion__section-heading > button > span')
      .first()
      .click({ force: true })
    cy.get('div > .govuk-accordion__section-content').should('not.be.visible')
  })
  it('displays second page of actions when click next', () => {
    cy.get('li').contains('Next').click()
    cy.url().should(
      'eq',
      Cypress.config('baseUrl') +
        `/${supplyChain.fields.slug}/strategic-actions?page=2`
    )
    cy.get('.govuk-accordion__section').should('have.length', 1)
  })
  it('displays first page of actions when click previous', () => {
    cy.get('li').contains('Previous').click()
    cy.url().should(
      'eq',
      Cypress.config('baseUrl') +
        `/${supplyChain.fields.slug}/strategic-actions?page=1`
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
