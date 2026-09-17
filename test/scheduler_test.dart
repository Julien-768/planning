// Tests du cœur métier (models/, services/ics_service.dart), sans dépendre
// de l'interface. Reproduisent les mêmes cas que tests/test_scheduler.py
// côté Python, pour vérifier que le portage se comporte identiquement.
import 'package:flutter_test/flutter_test.dart';
import 'package:planning_activites/models/activite.dart';
import 'package:planning_activites/models/calendrier_scolaire.dart';
import 'package:planning_activites/services/ics_service.dart';

CalendrierScolaire calendrierTest() {
  return CalendrierScolaire.fromJson({
    'annee': '2026-2027',
    'debut_annee': '2026-09-01',
    'fin_annee': '2027-07-02',
    'zones': {
      'B': {
        'label': 'Zone B',
        'academies': 'Strasbourg',
        'periodes': [
          {'nom': 'Toussaint', 'debut': '2026-10-17', 'fin': '2026-11-02'},
          {'nom': 'Noël', 'debut': '2026-12-19', 'fin': '2027-01-04'},
          {'nom': 'Hiver', 'debut': '2027-02-20', 'fin': '2027-03-08'},
          {'nom': 'Printemps', 'debut': '2027-04-17', 'fin': '2027-05-03'},
        ],
      },
    },
    'feries': [
      {'id': 'armistice', 'date': '2026-11-11', 'nom': '11 novembre'},
    ],
  });
}

void main() {
  group('calculerSeances', () {
    test('un mercredi de la Toussaint est retiré', () {
      final cal = calendrierTest();
      final activite = Activite(
        nom: 'Judo',
        jour: 2, // mercredi
        heureDebut: const HeureJour(17, 0),
        heureFin: const HeureJour(18, 0),
      );
      final exclus = cal.joursExclus('B');
      final seances = calculerSeances(activite, cal.debutAnnee, cal.finAnnee, exclus);

      final toussaint = DateTime(2026, 10, 21);
      expect(seances.retirees, contains(toussaint));
      expect(seances.conservees, isNot(contains(toussaint)));
    });

    test('la première séance conservée tombe hors vacances', () {
      final cal = calendrierTest();
      final activite = Activite(
        nom: 'Solfège',
        jour: 4, // vendredi
        heureDebut: const HeureJour(16, 30),
        heureFin: const HeureJour(17, 15),
      );
      final exclus = cal.joursExclus('B');
      final seances = calculerSeances(activite, cal.debutAnnee, cal.finAnnee, exclus);

      expect(seances.conservees.first.weekday, DateTime.friday);
      expect(exclus.contains(seances.conservees.first), isFalse);
    });

    test('une activité entièrement pendant les vacances ne produit aucune séance', () {
      final cal = calendrierTest();
      final activite = Activite(
        nom: 'Stage vacances',
        jour: 2,
        heureDebut: const HeureJour(17, 0),
        heureFin: const HeureJour(18, 0),
        premiereSeance: DateTime(2026, 10, 19),
        derniereSeance: DateTime(2026, 10, 30),
      );
      final exclus = cal.joursExclus('B');
      final seances = calculerSeances(activite, cal.debutAnnee, cal.finAnnee, exclus);

      expect(seances.conservees, isEmpty);
    });
  });

  group('genererIcs', () {
    test('contient une RRULE hebdomadaire et au moins une EXDATE', () {
      final cal = calendrierTest();
      final activite = Activite(
        nom: 'Judo',
        jour: 2,
        heureDebut: const HeureJour(17, 0),
        heureFin: const HeureJour(18, 0),
      );
      final contenu = genererIcs(activite, cal, 'B');

      expect(contenu, isNotNull);
      expect(contenu, contains('RRULE:FREQ=WEEKLY'));
      expect(contenu, contains('EXDATE'));
    });

    test('une activité sans séance retourne null', () {
      final cal = calendrierTest();
      final activite = Activite(
        nom: 'Stage vacances',
        jour: 2,
        heureDebut: const HeureJour(17, 0),
        heureFin: const HeureJour(18, 0),
        premiereSeance: DateTime(2026, 10, 19),
        derniereSeance: DateTime(2026, 10, 30),
      );
      expect(genererIcs(activite, cal, 'B'), isNull);
    });
  });

  group('slugifier', () {
    test('retire les accents et normalise', () {
      expect(slugifier('Solfège'), 'solfege');
      expect(slugifier('Éveil musical !'), 'eveil-musical');
    });
  });
}
