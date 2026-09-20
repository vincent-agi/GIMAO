"""Tests du service de notification email generique (TUS-013).

Utilise la fixture ``mailoutbox`` de pytest-django plutot que
``django.core.mail.outbox`` directement, pour garantir un outbox isole et
reinitialise entre chaque test.
"""

from notifications.services import send_notification


class TestSendNotification:
    def test_should_send_email_to_all_recipients(self, mailoutbox):
        sent = send_notification(
            event="echeance_controle_technique",
            recipients=["responsable@gimao.local", "gestionnaire@gimao.local"],
            context={
                "subject": "Contrôle technique à échéance",
                "titre": "Contrôle technique à échéance",
                "message": "Le véhicule AB-123-CD doit passer son contrôle technique.",
                "echeance": "2024-06-01",
            },
        )

        assert sent is True
        assert len(mailoutbox) == 1
        email = mailoutbox[0]
        assert email.subject == "Contrôle technique à échéance"
        assert email.to == ["responsable@gimao.local", "gestionnaire@gimao.local"]

    def test_should_include_html_alternative_with_context_values(self, mailoutbox):
        send_notification(
            event="echeance_controle_technique",
            recipients=["responsable@gimao.local"],
            context={
                "subject": "Alerte",
                "titre": "Titre du mail",
                "message": "Corps du message",
                "echeance": "2024-06-01",
                "lien": "https://gimao.local/vehicules/1",
            },
        )

        html_body = mailoutbox[0].alternatives[0][0]
        assert "Titre du mail" in html_body
        assert "Corps du message" in html_body
        assert "2024-06-01" in html_body
        assert "https://gimao.local/vehicules/1" in html_body

    def test_should_not_send_and_return_false_when_no_recipients(self, mailoutbox):
        sent = send_notification(event="echeance_controle_technique", recipients=[], context={})

        assert sent is False
        assert len(mailoutbox) == 0

    def test_should_fallback_subject_to_event_when_missing(self, mailoutbox):
        send_notification(
            event="echeance_controle_technique",
            recipients=["responsable@gimao.local"],
            context={"titre": "T", "message": "M"},
        )

        assert mailoutbox[0].subject == "echeance_controle_technique"
