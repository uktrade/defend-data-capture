Cypress.Commands.add(
    'label',
    {
        prevSubject: true,
    },
    (subject) => {
        cy.wrap(subject).invoke('attr', 'id').then((fieldID) => {
            return cy.get(`label[for="${fieldID}"]`);
        })
    }
);

Cypress.Commands.add(
    'hasDjangoCSRFToken',
    {
        prevSubject: true,
    },
    (subject) => {
        return cy.wrap(subject)
                 .get('input[type="hidden"][name="csrfmiddlewaretoken"]')
                 .should('exist')
                 .invoke('val')
                 .should('not.be.empty');
    }
)

Cypress.Commands.add(
    'gdsFormGroup',
    {
        prevSubject: true,
    },
    (subject) => {
        return cy.wrap(subject).get('govuk-form-group');
    }
)

Cypress.Commands.add(
    'gdsFormGroupError',
    {
        prevSubject: true,
    },
    (subject) => {
        return cy.wrap(subject).gdsFormGroup().should('have.class', 'govuk-form-group--error');
    }
)

Cypress.Commands.add(
    'gdsErrorSummary',
    {
        prevSubject: true,
    },
    (subject) => {
        return cy.wrap(subject).get('div.govuk-error-summary:first-of-type').should('exist');
    }
)

Cypress.Commands.add(
    'gdsErrorList',
    {
        prevSubject: true,
    },
    (subject) => {
        return cy.wrap(subject).get('.govuk-error-summary__list li a').should('exist');
    }
)

Cypress.Commands.add(
    'gdsFieldset',
    {
        prevSubject: true,
    },
    (subject) => {
        return cy.wrap(subject).get('fieldset.govuk-fieldset').should('exist');
    }
)



Cypress.Commands.add(
    'hasSubmitButton',
    {
        prevSubject: true,
    },
    (subject, text='Save and continue') => {
        return cy.wrap(subject).get('button[type="submit"]').contains('Save and continue');
    }
)

Cypress.Commands.add(
    'hasCancelLink',
    {
        prevSubject: true,
    },
    (subject, cancelURL='') => {
        return cy.wrap(subject).get('a.govuk-button.govuk-button--secondary').should('exist').contains('Cancel').within((theCancelLink) => {
            cy.root().should('have.attr', 'href', `/${cancelURL}`)
        });
    }
)

