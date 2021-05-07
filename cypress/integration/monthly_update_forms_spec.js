import supplyChains from '../fixtures/supplyChains.json'
import strategicActions from '../fixtures/strategicActions.json'
import strategicActionUpdates from '../fixtures/strategicActionUpdate.json'

const updatesByStrategicActionPK = strategicActionUpdates.reduce((accumulator, update) => {
  accumulator[update.fields.strategic_action] = update;
  return accumulator;
}, {});

const supplyChainsByPK = supplyChains.reduce((accumulator, supplyChain) => {
  accumulator[supplyChain.pk] = supplyChain;
  return accumulator;
}, {});

const strategicActionsForTest = strategicActions.reduce((accumulator, action) => {
  if (/a completion date/.test(action.fields.description)) {
    if (/^Has an update/.test(action.fields.description)) {
      const update = updatesByStrategicActionPK[action.pk],
        supplyChain = supplyChainsByPK[action.fields.supply_chain];
      accumulator.hasCompletionDate.hasUpdate = {
        'supplyChainSlug': supplyChain.fields.slug,
        'strategicActionSlug': action.fields.slug,
        'updateSlug': update.fields.slug,
        'updateContent': update.fields.content,
      };
    } else if (/^Has no update/.test(action.fields.description)) {
      const supplyChain = supplyChainsByPK[action.fields.supply_chain];
      if (/will be submitted with errors/.test(action.fields.description)) {
        accumulator.hasCompletionDate.forErrors = {
          'supplyChainSlug': supplyChain.fields.slug,
          'strategicActionSlug': action.fields.slug,
        };
      } else {
        accumulator.hasCompletionDate.noUpdate = {
          'supplyChainSlug': supplyChain.fields.slug,
          'strategicActionSlug': action.fields.slug,
        };
      }
    }
  } else if (/no completion date/.test(action.fields.description)) {
    if (/^Has an update/.test(action.fields.description)) {
      const update = updatesByStrategicActionPK[action.pk],
          supplyChain = supplyChainsByPK[action.fields.supply_chain];
      accumulator.noCompletionDate.hasUpdate = {
        'supplyChainSlug': supplyChain.fields.slug,
        'strategicActionSlug': action.fields.slug,
        'updateSlug': update.fields.slug,
        'updateContent': update.fields.content,
      };
    } else if (/^Has no update/.test(action.fields.description)) {
      const supplyChain = supplyChainsByPK[action.fields.supply_chain];
      if (/will be submitted with errors/.test(action.fields.description)) {
        accumulator.noCompletionDate.forErrors = {
          'supplyChainSlug': supplyChain.fields.slug,
          'strategicActionSlug': action.fields.slug,
        };
      } else {
        accumulator.noCompletionDate.noUpdate = {
          'supplyChainSlug': supplyChain.fields.slug,
          'strategicActionSlug': action.fields.slug,
        };
      }
    }
  }
  return accumulator;
}, {
  'hasCompletionDate': {
    'hasUpdate': [],
    'noUpdate': []
  },
  'noCompletionDate': {
    'hasUpdate': [],
    'noUpdate': []
  }
});

const today = new Date();
const isoToday = today.toISOString();
const todayMatches = /(\d{4})-(\d{2})/.exec(isoToday);
const todayMonth = todayMatches[2];
const todayYear = todayMatches[1];
const todaySlug = `${todayMonth}-${todayYear}`

const valuesToEnter = {
  info: {
    content: 'This is the text entered for the content field.'
  },
  timing: {
    Yes: {
      date: {
        day: 22,
        month: 11,
        year: 2023,
        monthString: 'November'
      },
    },
    No: {
      options: {
        durations: [
          [3, '3 months'],
          [6, '6 months'],
          [12, '1 year'],
          [24, '2 years'],
          [0, 'Ongoing'],
        ]
      }
    }
  },
  status: {
    options: {
      Red: {
        reason: 'This is the reason the status is RED',
        datechange: ['Yes', 'No']
      },
      Amber: {
        reason: 'This is the reason the status is AMBER',
      },
      Green: null,
    }
  },
  revisedtiming: {
    yes: {
      date: {
        day: 22,
        month: 11,
        year: 2023,
      },
    },
    no: {
      options: {
        durations: [
          [3, '3 months'],
          [6, '6 months'],
          [12, '1 year'],
          [24, '2 years'],
          [0, 'Ongoing'],
        ]
      }
    },
    reason: 'This is the reason the completion date changed'
  },
}

Cypress.Cookies.debug(true);

describe('Testing monthly update forms', () => {
  context('for a strategic action', function() {
    context('that has no target completion date', function() {
      context('with an update from the previous month', function() {
        beforeEach(() => {
          Cypress.Cookies.preserveOnce('csrftoken', 'sessionid')
          cy.wrap(strategicActionsForTest.noCompletionDate.hasUpdate.supplyChainSlug).as('supplyChainSlug')
          cy.wrap(strategicActionsForTest.noCompletionDate.hasUpdate.strategicActionSlug).as('strategicActionSlug')
          cy.wrap(strategicActionsForTest.noCompletionDate.hasUpdate.updateSlug).as('monthlyUpdateSlug')
          cy.wrap(strategicActionsForTest.noCompletionDate.hasUpdate.updateContent).as('updateContent')
          cy.wrap(todaySlug).as('todaySlug')
          cy.url().as('pageURL')
        });
        context('starting a new monthly update', function() {
          it('successfully creates a new update and redirects to its Update Info page', function() {
            cy.visit(`http://localhost:8001/${this.supplyChainSlug}/strategic-actions/${this.strategicActionSlug}/update/start/`)
            cy.url().should('eq', `http://localhost:8001/${this.supplyChainSlug}/strategic-actions/${this.strategicActionSlug}/update/${this.todaySlug}/info/`)
            cy.injectAxe()
          })
        })
        context(`The Update Info page ${this.pageURL}`, function() {
          it('has no accessibility issues', () => {
            cy.runA11y()
          })
          context('The Update Info breadcrumbs', function() {
            beforeEach(() => {
              cy.get('nav.moj-sub-navigation').as('theBreadcrumbs')
            })
            it('should be present', () => {
              cy.get('@theBreadcrumbs').should('exist')
            })
            it ('should contain an ordered list', () => {
              cy.get('@theBreadcrumbs').get('ol.moj-sub-navigation__list').should('exist')
            })
            context('The individual breadcrumbs in the ordered list should be', function() {
              beforeEach(() => {
                cy.get('nav.moj-sub-navigation ol.moj-sub-navigation__list li').as('theBreadcrumbItems')
              })
              it('the "Update information" link', () => {
                cy.get('@theBreadcrumbItems').eq(0).contains('1. Update information')
              })
              it('the "Timing" link', () => {
                cy.get('@theBreadcrumbItems').eq(1).contains('2. Timing')
              })
              it('the "Action status" link', () => {
                cy.get('@theBreadcrumbItems').eq(2).contains('3. Action status')
              })
              it('the "Confirm" link', () => {
                cy.get('@theBreadcrumbItems').eq(3).contains('4. Confirm')
              })
            })
            context('The link marked as the current page should be', () => {
              beforeEach(() => {
                cy.get('nav.moj-sub-navigation ol.moj-sub-navigation__list li').as('theBreadcrumbItems')
              })
              it('the "Update information" link', () => {
                cy.get('@theBreadcrumbItems').eq(0).within(() => {
                  cy.root().get('a').should('have.attr', 'aria-current', 'page')
                })
              })
            })
          })
          context('The Update Info page content', function() {
            it('has the correct page header', () => {
              cy.get('h1').contains(
                  'Strategic action monthly update'
              )
            })
            it('shows the previous update', function() {
              cy.get('.app-dit-panel h2:first').contains('Last update')
              cy.get('.app-dit-panel h2:first + p').contains(`${this.updateContent}`)
            })
          })
          context('The Update Info form', () => {
            beforeEach(() => {
              cy.get('main form').as('theForm')
              cy.wrap(valuesToEnter.info).as('valuesToEnter')
            })
            it('is there', () => {
              cy.get("@theForm").should('exist')
            })
            it('should have a CSRF token', () => {
              cy.get("@theForm").hasDjangoCSRFToken()
            })
            it('should have a textarea for the "content" field labelled "Latest monthly update"', () => {
              cy.get("@theForm").within((theForm) => {
                cy.get('textarea[name="content"]').label().should('contain.text', 'Latest monthly update')
              })
            })
            it('should have a submit button saying "Save and continue"', () => {
              cy.get('@theForm').hasSubmitButton()
            })
            it('should have a cancel link saying "Cancel" going back to the supply chain page', function() {
              cy.get('@theForm').hasCancelLink(`${this.supplyChainSlug}`)
              // cy.get('@theForm').within(function(theForm) {
              //   cy.get('a.govuk-button.govuk-button--secondary').contains('Cancel').within((theCancelLink) => {
              //     cy.root().should('have.attr', 'href', `/${this.supplyChainSlug}`)
              //   })
              // })
            })
            context('When submitted with the content field filled out', function() {
              before(() => {
                // ensure we start with a clean slate
                cy.reload(true, {log: true})
              })
              beforeEach(() => {
                cy.get('@valuesToEnter').as('valuesToEnter')
              })
              it('should go to the "Timing" page when saved', function() {
                cy.get('@theForm').within(function(theForm) {
                  cy.get('textarea[name="content"]').type(`${this.valuesToEnter.content}`)
                  cy.location('pathname').invoke('split', '/').its(5).as('strategicActionUpdateID')
                  cy.get('@strategicActionUpdateID').then(function(strategicActionUpdateID) {
                    cy.get('button[type="submit"]').click()
                    cy.url().should('eq', `http://localhost:8001/${this.supplyChainSlug}/strategic-actions/${this.strategicActionSlug}/update/${this.todaySlug}/timing/`)
                    cy.injectAxe()
                  })
                })
              })
            })
          })
        })
        context('The Timing page', () => {
          beforeEach(() => {
            Cypress.Cookies.preserveOnce('csrftoken', 'sessionid')
            cy.get('main form').as('theForm')
          })
          it.skip('has no accessibility issues - NEEDS CHECKING FOR POSSIBLE FALSE POSITIVE', () => {
            cy.runA11y()
          })
          context('The Timing breadcrumbs', function() {
            beforeEach(() => {
              cy.get('nav.moj-sub-navigation').as('theBreadcrumbs')
            })
            it ('should contain an ordered list', () => {
              cy.get('@theBreadcrumbs').get('ol.moj-sub-navigation__list').should('exist')
            })
            context('The individual breadcrumbs in the ordered list should be', function() {
              beforeEach(() => {
                cy.get('nav.moj-sub-navigation ol.moj-sub-navigation__list li').as('theBreadcrumbItems')
              })
              it('the "Update information" link', () => {
                cy.get('@theBreadcrumbItems').eq(0).contains('1. Update information')
              })
              it('the "Timing" link', () => {
                cy.get('@theBreadcrumbItems').eq(1).contains('2. Timing')
              })
              it('the "Action status" link', () => {
                cy.get('@theBreadcrumbItems').eq(2).contains('3. Action status')
              })
              it('the "Confirm" link', () => {
                cy.get('@theBreadcrumbItems').eq(3).contains('4. Confirm')
              })
            })
            context('The link marked as the current page should be', () => {
              beforeEach(() => {
                cy.get('nav.moj-sub-navigation ol.moj-sub-navigation__list li').as('theBreadcrumbItems')
              })
              it('the "Timing" link', () => {
                cy.get('@theBreadcrumbItems').eq(1).within(() => {
                  cy.root().get('a').should('have.attr', 'aria-current', 'page')
                })
              })
            })
          })
          context('The Timing page content', function() {
            it('has the correct page header', () => {
              cy.get('h1').contains(
                  'Strategic action monthly update'
              )
            })
            it ('warns that there is no expected completion date', () => {
              cy.get('h1 ~ .govuk-warning-text').should('exist').contains("There's no expected completion date for this action.")
            })
          })
          context('The Timing form', () => {
            it('is there', () => {
              cy.get("@theForm").should('exist')
            })
            it('should have a CSRF token', () => {
              cy.get("@theForm").hasDjangoCSRFToken()
            })
            it('should have a submit button saying "Save and continue"', () => {
              cy.get('@theForm').hasSubmitButton()
            })
            it('should have a cancel link saying "Cancel" going back to the supply chain page', function() {
              cy.get('@theForm').hasCancelLink(`${this.supplyChainSlug}`)
            })
            it ('should have a fieldset with legend asking if there is a completion date', () => {
              cy.get('@theForm').get('fieldset legend h2').contains('Is there an expected completion date?')
            })
            context('The radio buttons asking if there is an expected completion date', function() {
              beforeEach(() => {
                cy.get('@theForm').get('div.govuk-form-group > fieldset.govuk-fieldset > *[data-module="govuk-radios"] > .govuk-radios__item > input[type="radio"]').as('theRadioButtons')
              })
              it('should be present', () => {
                cy.get('@theRadioButtons').should('exist')
              })
              it('should be two in number', () => {
                cy.get('@theRadioButtons').should('have.length', 2)
              })
              it('the first should have the label "Yes"', () => {
                cy.get('@theRadioButtons').eq(0).siblings('label').eq(0).contains('Yes')
              })
              it('the second should have the label "No"', () => {
                cy.get('@theRadioButtons').eq(1).siblings('label').eq(0).contains('No')
              })
              context('The "Yes" option', function() {
                before(() => {
                  // ensure we start with a clean slate
                  cy.reload(true, {log: true})
                })
                beforeEach(() => {
                  cy.get('@theForm').get('div.govuk-form-group > fieldset.govuk-fieldset > *[data-module="govuk-radios"] > .govuk-radios__item > input[type="radio"]').as('theRadioButtons')
                  cy.get('@theRadioButtons').eq(0).as('theYesOption')
                  cy.get('@theRadioButtons').eq(1).as('theNoOption')
                })
                it('should initially be unchecked', () => {
                  cy.get('@theYesOption').should('not.be.checked')
                })
                it('its subject should initially be hidden', () => {
                  cy.get('@theYesOption').invoke('attr', 'aria-controls').then((subjectID) => {
                    cy.get(`#${subjectID}`).should('be.hidden')
                  })
                })
                context('When it is selected, it', function() {
                  it('should make the date entry fields visible', () => {
                    cy.get('@theYesOption').click()
                    cy.get('@theYesOption').invoke('attr', 'aria-controls').then((subjectID) => {
                      cy.get(`#${subjectID}`).should('be.visible')
                    })
                  })
                  it('the approximate timing or ongoing fields should remain hidden', () => {
                    cy.get('@theNoOption').invoke('attr', 'aria-controls').then((subjectID) => {
                      cy.get(`#${subjectID}`).should('be.hidden')
                    })
                  })
                  context('The revealed date entry fields', function() {
                    beforeEach(() => {
                      cy.get('@theYesOption').invoke('attr', 'aria-controls').then((subjectID) => {
                        cy.get(`#${subjectID}`).as('theDateSection')
                      })
                    })
                    it ('should have all its date fields and labels for day, month, and year', () => {
                      cy.get('@theDateSection').within(() => {
                        cy.get('input').eq(0).should('have.attr', 'name', 'True-changed_target_completion_date_day')
                        cy.get('input').eq(0).invoke('attr', 'id').then((fieldID) => {
                          cy.get(`label[for="${fieldID}"]`).should('exist').contains('Day')
                        })
                        cy.get('input').eq(1).should('have.attr', 'name', 'True-changed_target_completion_date_month')
                        cy.get('input').eq(1).invoke('attr', 'id').then((fieldID) => {
                          cy.get(`label[for="${fieldID}"]`).should('exist').contains('Month')
                        })
                        cy.get('input').eq(2).should('have.attr', 'name', 'True-changed_target_completion_date_year')
                        cy.get('input').eq(2).invoke('attr', 'id').then((fieldID) => {
                          cy.get(`label[for="${fieldID}"]`).should('exist').contains('Year')
                        })
                      })
                    })
                  })
                })
              })
              context('The "No" option', function() {
                before(() => {
                  // ensure we start with a clean slate
                  cy.reload(true, {log: true})
                })
                beforeEach(() => {
                  cy.get('@theForm').get('div.govuk-form-group > fieldset.govuk-fieldset > *[data-module="govuk-radios"] > .govuk-radios__item > input[type="radio"]').as('theRadioButtons')
                  cy.get('@theRadioButtons').eq(0).as('theYesOption')
                  cy.get('@theRadioButtons').eq(1).as('theNoOption')
                })
                it('should initially be unchecked', () => {
                  cy.get('@theNoOption').should('not.be.checked')
                })
                it('its subject should initially be hidden', () => {
                  cy.get('@theNoOption').invoke('attr', 'aria-controls').then((subjectID) => {
                    cy.get(`#${subjectID}`).should('exist')
                    cy.get(`#${subjectID}`).should('be.hidden')
                  })
                })
                context('When it is selected, it', function() {
                  it('should make the approximate timing or ongoing fields visible', () => {
                    cy.get('@theNoOption').click()
                    cy.get('@theNoOption').invoke('attr', 'aria-controls').then((subjectID) => {
                      cy.get(`#${subjectID}`).should('be.visible')
                    })
                  })
                  it('the date entry fields should remain hidden', () => {
                    cy.get('@theYesOption').invoke('attr', 'aria-controls').then((subjectID) => {
                      cy.get(`#${subjectID}`).should('be.hidden')
                    })
                  })
                  context('The revealed approximate timing or ongoing fields', function() {
                    beforeEach(() => {
                      cy.get('@theNoOption').invoke('attr', 'aria-controls').then((subjectID) => {
                        cy.get(`#${subjectID}`).as('theApproximateTimingSection')
                      })
                      cy.wrap(valuesToEnter.timing.No.options.durations).as('approximateTimings')
                    })
                    it('should have radio buttons and labels for 3 months to 2 years or Ongoing', () => {
                      cy.get('@theApproximateTimingSection').within(() => {
                        cy.get('@approximateTimings').then((approximateTimings) => {
                          approximateTimings.forEach((approximateTiming, index) => {
                            cy.get('input').eq(index).should('have.attr', 'name', 'False-surrogate_is_ongoing')
                            cy.get('input').eq(index).should('have.attr', 'value', approximateTiming[0]).invoke('attr', 'id').then((fieldID) => {
                              cy.get(`label[for="${fieldID}"]`).should('exist').contains(approximateTiming[1])
                            })
                          })
                        })
                      })
                    })
                  })
                })
                context('Selecting a duration and submitting the form', function() {
                  it('should go to the "Delivery status" page when saved', function() {
                    cy.get('@theNoOption').click()
                    cy.get('@theNoOption').invoke('attr', 'aria-controls').then((subjectID) => {
                      cy.get(`#${subjectID}`).get('input[type="radio"]').eq(2).click()
                      cy.location('pathname').invoke('split', '/').its(5).as('strategicActionUpdateID')
                      cy.get('@strategicActionUpdateID').then(function(strategicActionUpdateID) {
                        cy.get('button[type="submit"]').click()
                        cy.url().should('eq', `http://localhost:8001/${this.supplyChainSlug}/strategic-actions/${this.strategicActionSlug}/update/${this.todaySlug}/delivery-status/`)
                        cy.injectAxe()
                      })
                    })
                  })
                })
              })
            })
          })
        })
        context('The Delivery Status page', () => {
          beforeEach(() => {
            Cypress.Cookies.preserveOnce('csrftoken', 'sessionid')
          })
          it.skip('has no accessibility issues - NEEDS CHECKING FOR POSSIBLE FALSE POSITIVE', () => {
            cy.runA11y()
          })
          context('The Delivery Status breadcrumbs', function() {
            beforeEach(() => {
              cy.get('nav.moj-sub-navigation').as('theBreadcrumbs')
            })
            context('The individual breadcrumbs in the ordered list should be', function() {
              beforeEach(() => {
                cy.get('nav.moj-sub-navigation ol.moj-sub-navigation__list li').as('theBreadcrumbItems')
              })
              it('the "Update information" link', () => {
                cy.get('@theBreadcrumbItems').eq(0).contains('1. Update information')
              })
              it('the "Timing" link', () => {
                cy.get('@theBreadcrumbItems').eq(1).contains('2. Timing')
              })
              it('the "Action status" link', () => {
                cy.get('@theBreadcrumbItems').eq(2).contains('3. Action status')
              })
              it('the "Confirm" link', () => {
                cy.get('@theBreadcrumbItems').eq(3).contains('4. Confirm')
              })
            })
            context('The link marked as the current page should be', () => {
              beforeEach(() => {
                cy.get('nav.moj-sub-navigation ol.moj-sub-navigation__list li').as('theBreadcrumbItems')
              })
              it('the "Delivery status" link', () => {
                cy.get('@theBreadcrumbItems').eq(2).within(() => {
                  cy.root().get('a').should('have.attr', 'aria-current', 'page')
                })
              })
            })
          })
          context('The Delivery Status page content', function() {
            it('has the correct page header', () => {
              cy.get('h1').contains(
                  'Strategic action monthly update'
              )
            })
            // it('shows the delivery status for the previous month', function() {
            //   cy.get('h2:first').contains('Last update')
            //   cy.get('h2:first + p').contains(`${this.updateContent}`)
            // })
          })
          context('The Delivery Status form', () => {
            beforeEach(() => {
              cy.get('main form').as('theForm')
            })
            it('is there', () => {
              cy.get("@theForm").should('exist')
            })
            it('should have a CSRF token', () => {
              cy.get("@theForm").hasDjangoCSRFToken()
            })
            it('should have a submit button saying "Save and continue"', () => {
              cy.get('@theForm').hasSubmitButton()
            })
            it('should have a cancel link saying "Cancel" going back to the supply chain page', function() {
              cy.get('@theForm').hasCancelLink(`${this.supplyChainSlug}`)
            })
            context('the radio buttons asking for the current delivery status', function() {
              beforeEach(() => {
                cy.get('@theForm').get('div.govuk-form-group > fieldset.govuk-fieldset > *[data-module="govuk-radios"] > .govuk-radios__item').as('theRadioItems')
                cy.get('@theRadioItems').get('input[type="radio"]').as('theRadioButtons')
                cy.get('@theRadioButtons').get('.govuk-hint').as('theRadioHints')
              })
              it('should be three in number', () => {
                cy.get('@theRadioButtons').should('have.length', 3)
                cy.get('@theRadioHints').should('have.length', 3)
              })
              it('the first should have the label "Green" and the correct hint text', () => {
                cy.get('@theRadioButtons').eq(0).siblings('label').eq(0).contains('Green')
                cy.get('@theRadioHints').eq(0).contains('Delivery is on track with no issues')
              })
              it('the second should have the label "Amber" and the correct hint text', () => {
                cy.get('@theRadioButtons').eq(1).siblings('label').eq(0).contains('Amber')
                cy.get('@theRadioHints').eq(1).contains("There's a potential risk to delivery that needs monitoring.")
              })
              it('the third should have the label "Red" and the correct hint text', () => {
                cy.get('@theRadioButtons').eq(2).siblings('label').eq(0).contains('Red')
                cy.get('@theRadioHints').eq(2).contains("There is an issue with delivery of an action. This will require escalation and further support. There is a potential risk to the expected completion date.")
              })
              context('The "Amber" option', function() {
                beforeEach(() => {
                  cy.get('@theRadioButtons').eq(1).as('amberOption')
                })
                it('displays the potential risks textbox when selected', function() {
                  cy.get('@amberOption').click()
                  cy.get('@amberOption').invoke('attr', 'aria-controls').then((subjectID) => {
                      cy.get(`#${subjectID}`).should('be.visible')
                      cy.get(`#${subjectID}`).children(0).children('label').should('contain', 'Explain potential risk')
                      cy.get(`#${subjectID}`).children(0).children('textarea').should('be.visible')
                    })
                })
              })
              context('The "Red" option', function() {
                beforeEach(() => {
                  cy.get('@theRadioButtons').eq(2).as('redOption')
                })
                it('displays the Explain issue label and textbox when selected', function() {
                  cy.get('@redOption').click()
                  cy.get('@redOption').invoke('attr', 'aria-controls').then((subjectID) => {
                      cy.get(`#${subjectID}`).should('be.visible')
                      cy.get(`#${subjectID}`).children(0).children('label').should('contain', 'Explain issue')
                      cy.get(`#${subjectID}`).children(0).children('textarea').should('be.visible')
                    })
                })
                it.skip('displays the date change label and radios', function() {
                  cy.get('@redOption').click()
                  cy.get('@redOption').invoke('attr', 'aria-controls').then((subjectID) => {
                      cy.get(`#${subjectID} > .govuk-form-group > fieldset > .govuk-radios > .govuk-radios__item`).as('dateChangeRadios')
                      cy.get(`#${subjectID}`).should('be.visible')
                      cy.get(`#${subjectID} > .govuk-form-group > fieldset > legend > h3`).should('contain', 'Will the estimated completion date change?')
                      cy.get('@dateChangeRadios').should('have.length', 2)
                      cy.get('@dateChangeRadios').eq(0).should('contain', 'Yes')
                      cy.get('@dateChangeRadios').eq(1).should('contain', 'No')
                    })
                })
              })
            })
            // context('the error messages', function() {
            //   before(() => {
            //     // ensure we start with a clean slate
            //     cy.reload(true, {log: true})
            //   })
            //   it('should display error summary when submitted without selecting a status radio', () => {
            //     cy.contains('Save and continue').click()
            //   })
            // })
            //
          })
        })
      })
      context('without an update from the previous month', function() {
        beforeEach(() => {
          Cypress.Cookies.preserveOnce('csrftoken', 'sessionid')
          cy.wrap(strategicActionsForTest.noCompletionDate.noUpdate.supplyChainSlug).as('supplyChainSlug')
          cy.wrap(strategicActionsForTest.noCompletionDate.noUpdate.strategicActionSlug).as('strategicActionSlug')
          cy.wrap(strategicActionsForTest.noCompletionDate.noUpdate.updateSlug).as('monthlyUpdateSlug')
          cy.wrap(strategicActionsForTest.noCompletionDate.noUpdate.updateContent).as('updateContent')
          cy.wrap(todaySlug).as('todaySlug')
        });
        context('starting a new monthly update', function() {
          it('successfully creates a new update and redirects to its Update Info page', function() {
            cy.visit(`http://localhost:8001/${this.supplyChainSlug}/strategic-actions/${this.strategicActionSlug}/update/start/`)
            cy.url().should('eq', `http://localhost:8001/${this.supplyChainSlug}/strategic-actions/${this.strategicActionSlug}/update/${this.todaySlug}/info/`)
            cy.injectAxe()
          })
        })
        context('The Update Info page', function() {
          it('has no accessibility issues', () => {
            cy.runA11y()
          })
          context('The Update Info page content', function() {
            it('does not include a previous update', function() {
              cy.get('.app-dit-panel').should('not.exist')
            })
          })
        })
      })
    })
    context('that does have a target completion date', function() {
      context('with an update from the previous month', function() {
        beforeEach(() => {
          Cypress.Cookies.preserveOnce('csrftoken', 'sessionid')
          cy.wrap(strategicActionsForTest.noCompletionDate.noUpdate.supplyChainSlug).as('supplyChainSlug')
          cy.wrap(strategicActionsForTest.noCompletionDate.noUpdate.strategicActionSlug).as('strategicActionSlug')
          cy.wrap(strategicActionsForTest.noCompletionDate.noUpdate.updateSlug).as('monthlyUpdateSlug')
          cy.wrap(strategicActionsForTest.noCompletionDate.noUpdate.updateContent).as('updateContent')
          cy.wrap(todaySlug).as('todaySlug')
        });
        context('starting a new monthly update', function() {
          it('successfully creates a new update and redirects to its Update Info page', function() {
            cy.visit(`http://localhost:8001/${this.supplyChainSlug}/strategic-actions/${this.strategicActionSlug}/update/start/`)
            cy.url().should('eq', `http://localhost:8001/${this.supplyChainSlug}/strategic-actions/${this.strategicActionSlug}/update/${this.todaySlug}/info/`)
            cy.injectAxe()
          })
        })
      })
      context('without an update from the previous month', function() {
        beforeEach(() => {
          Cypress.Cookies.preserveOnce('csrftoken', 'sessionid')
          cy.wrap(strategicActionsForTest.noCompletionDate.noUpdate.supplyChainSlug).as('supplyChainSlug')
          cy.wrap(strategicActionsForTest.noCompletionDate.noUpdate.strategicActionSlug).as('strategicActionSlug')
          cy.wrap(strategicActionsForTest.noCompletionDate.noUpdate.updateSlug).as('monthlyUpdateSlug')
          cy.wrap(strategicActionsForTest.noCompletionDate.noUpdate.updateContent).as('updateContent')
          cy.wrap(todaySlug).as('todaySlug')
        });
        context('starting a new monthly update', function() {
          it('successfully creates a new update and redirects to its Update Info page', function() {
            cy.visit(`http://localhost:8001/${this.supplyChainSlug}/strategic-actions/${this.strategicActionSlug}/update/start/`)
            cy.url().should('eq', `http://localhost:8001/${this.supplyChainSlug}/strategic-actions/${this.strategicActionSlug}/update/${this.todaySlug}/info/`)
            cy.injectAxe()
          })
        })
      })
    })
  })
})


describe('Testing validation errors in the monthly update forms', () => {
  context('for a strategic action', function() {
      context('that has no target completion date', function() {
        beforeEach(() => {
          Cypress.Cookies.preserveOnce('csrftoken', 'sessionid')
          cy.wrap(strategicActionsForTest.noCompletionDate.forErrors.supplyChainSlug).as('supplyChainSlug')
          cy.wrap(strategicActionsForTest.noCompletionDate.forErrors.strategicActionSlug).as('strategicActionSlug')
          cy.wrap(strategicActionsForTest.noCompletionDate.forErrors.updateSlug).as('monthlyUpdateSlug')
          cy.wrap(strategicActionsForTest.noCompletionDate.forErrors.updateContent).as('updateContent')
          cy.wrap(todaySlug).as('todaySlug')
        });
        it ('starts a new update', function() {
          cy.visit(`http://localhost:8001/${this.supplyChainSlug}/strategic-actions/${this.strategicActionSlug}/update/start/`)
        })
        context('The Update Info form', () => {
          beforeEach(() => {
            cy.get('main form').as('theForm')
          })
          context('When submitted without entering any text in the content field', function() {
            before(() => {
              // ensure we start with a clean slate
              cy.reload(true, {log: true})
            })
            context('should redisplay the page', () => {
              it('with an error summary at the top', function() {
                cy.url().then((url) => {
                  /**
                   * This can't happen 'within' the form
                   * as once the submit button is clicked,
                   * the page with the form is replaced
                   * but that page has a new form instance as far as the DOM is concerned
                   * so we need to be able to select the (new) form
                   */
                  cy.get('@theForm').get('button[type="submit"]').click()
                  cy.url().should('eq', url)
                  // cy.get('main').hasGDSErrorSummary().hasGDSErrorList()
                  // cy.get('main').within(() => {
                  //   cy.get('div.govuk-error-summary:first-of-type').should('exist').within(() => {
                  //     cy.get('.govuk-error-summary__list li a').should('exist')
                  //   })
                  // })
                })
              })
              it('with an error message on the field', function() {
                cy.url().then((url) => {
                  /**
                   * This can't happen 'within' the form
                   * as once the submit button is clicked,
                   * the page with the form is replaced
                   * but that page has a new form instance as far as the DOM is concerned
                   * so we need to be able to select the (new) form
                   */
                  cy.get('@theForm').get('button[type="submit"]').click()
                  cy.url().should('eq', url)
                  cy.get('main form').within(() => {
                    cy.get('.govuk-form-group--error').should('exist')
                    cy.get('.govuk-error-message').should('exist')
                  })
                })
              })
            })
          })
        })
        context('The Timing form', () => {
          beforeEach(() => {
            Cypress.Cookies.preserveOnce('csrftoken', 'sessionid')
            cy.wrap(strategicActionsForTest.noCompletionDate.forErrors.supplyChainSlug).as('supplyChainSlug')
            cy.wrap(strategicActionsForTest.noCompletionDate.forErrors.strategicActionSlug).as('strategicActionSlug')
            cy.wrap(strategicActionsForTest.noCompletionDate.forErrors.updateSlug).as('monthlyUpdateSlug')
            cy.wrap(strategicActionsForTest.noCompletionDate.forErrors.updateContent).as('updateContent')
            cy.wrap(todaySlug).as('todaySlug')
          })
          context('when the expected completion date is known', function() {
            before(() => {
              // ensure we start with a clean slate
              cy.reload(true, {log: true})
              cy.get('@theForm')
            })

          })
          context('When submitted without selecting "Yes" or "No"', function() {
            before(function() {
              // ensure we start with a clean slate
              cy.visit(`http://localhost:8001/${this.supplyChainSlug}/strategic-actions/${this.strategicActionSlug}/update/${this.todaySlug}/timing/`)
              cy.get('main form').as('theForm')
            })
            context('should redisplay the page', function() {
              it('with an error summary at the top and an error message on the field', function() {
                cy.url().then(function(url) {
                  /**
                   * This can't happen 'within' the form
                   * as once the submit button is clicked,
                   * the page with the form is replaced
                   * but that page has a new form instance as far as the DOM is concerned
                   * so we need to be able to select the (new) form
                   */
                  cy.get('main form').get('button[type="submit"]').click()
                  cy.url().should('eq', url)
                  cy.get('main').gdsErrorSummary().gdsErrorList()
                  cy.get('main form').within(() => {
                    cy.get('.govuk-error-message').should('exist')
                  })
                })
              })
            })
          })
        })
      })
      context('that does have a target completion date', function() {})
  })
})
