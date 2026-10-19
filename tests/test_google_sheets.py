import asyncio
import os
import unittest
from unittest.mock import Mock, patch

import app

HEADERS = ['Interviewee First Name', 'Interviewee Last Name']


class GoogleSheetsTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            'GOOGLE_SHEET_ID': 'test-spreadsheet',
            'GOOGLE_OBSERVATIONS_SHEET_NAME': 'Observations',
            'GOOGLE_INTERVIEWEES_SHEET_NAME': 'Interviewees',
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        app._candidate_cache.update(key=None, names=[], error=None, expires_at=0)

    def test_parse_names(self):
        self.assertEqual(app.parse_candidate_rows([
            [' Interviewee Last Name ', 'Interviewee First Name'],
            [' Lovelace ', ' Ada '], [], ['Lovelace', 'Ada'], ['Solo'],
        ]), ['Ada Lovelace', 'Solo'])
        self.assertEqual(app.parse_candidate_rows([HEADERS, [], ['', '']]), [])
        for rows in ([], [['First Name', 'Last Name']], [HEADERS + [HEADERS[0]]]):
            with self.assertRaises(ValueError):
                app.parse_candidate_rows(rows)

    def test_cache_refresh_failure_recovery_and_empty_list(self):
        book = Mock()
        sheet = book.worksheet.return_value
        sheet.get_all_values.side_effect = [
            [HEADERS, ['Ada', 'Lovelace']],
            RuntimeError('offline'),
            [HEADERS, ['Grace', 'Hopper']],
            [HEADERS],
        ]
        with patch.object(app, 'get_spreadsheet', return_value=book), patch.object(app, 'monotonic') as clock, patch.object(app.logger, 'exception'):
            clock.return_value = 100
            self.assertEqual(app.candidate_data(), (['Ada Lovelace'], None))
            clock.return_value = 159
            self.assertEqual(app.candidate_data(), (['Ada Lovelace'], None))
            self.assertEqual(sheet.get_all_values.call_count, 1)
            clock.return_value = 161
            names, error = app.candidate_data()
            self.assertEqual(names, ['Ada Lovelace'])
            self.assertIn('last successfully loaded', error)
            clock.return_value = 180
            app.candidate_data()
            self.assertEqual(sheet.get_all_values.call_count, 2)
            clock.return_value = 222
            self.assertEqual(app.candidate_data(), (['Grace Hopper'], None))
            clock.return_value = 283
            self.assertEqual(app.candidate_data()[0], [])
            book.worksheet.assert_called_with('Interviewees')

    def test_initial_failure_and_configuration_change(self):
        with patch.object(app, 'get_spreadsheet', side_effect=RuntimeError('offline')), patch.object(app.logger, 'exception'):
            names, error = app.candidate_data()
            self.assertEqual(names, [])
            self.assertTrue(error)
        app._candidate_cache['names'] = ['Old Candidate']
        with patch.dict(os.environ, {'GOOGLE_INTERVIEWEES_SHEET_NAME': 'New Tab'}), patch.object(app, 'get_spreadsheet', side_effect=RuntimeError('offline')), patch.object(app.logger, 'exception'):
            self.assertEqual(app.candidate_data()[0], [])

    def test_observation_tab_and_submission(self):
        book = Mock()
        with patch.object(app, 'get_spreadsheet', return_value=book):
            sheet = app.get_sheet()
            book.worksheet.assert_called_once_with('Observations')
            with patch.dict(os.environ, {'GOOGLE_OBSERVATIONS_SHEET_NAME': 'Interviewees'}):
                with self.assertRaises(ValueError):
                    app.get_sheet()
        entry = dict(candidate='Test', round='Round 1', room='Test', observer_name='Test',
                     teamwork=1, initiative=1, personal_rep=1, work_with='Yes', comments='', submitted_to_sheets=False)
        with patch.object(app, 'observations', [entry]), patch.object(app, 'get_sheet', return_value=sheet), patch.object(app, 'candidate_data', return_value=(['Test'], None)), patch.object(app.templates, 'TemplateResponse') as render:
            asyncio.run(app.final_submit(None))
            self.assertTrue(entry['submitted_to_sheets'])
            self.assertEqual(sheet.append_rows.call_args.kwargs['table_range'], 'A1:J')
            self.assertIsNone(render.call_args.kwargs['context']['error_msg'])
            entry['submitted_to_sheets'] = False
            sheet.append_rows.side_effect = RuntimeError('offline')
            asyncio.run(app.final_submit(None))
            self.assertFalse(entry['submitted_to_sheets'])
            self.assertTrue(render.call_args.kwargs['context']['error_msg'])

    def test_warning_renders(self):
        from starlette.requests import Request
        request = Request({'type': 'http', 'method': 'GET', 'path': '/', 'headers': [], 'scheme': 'http', 'server': ('test', 80), 'router': app.app.router})
        with patch.object(app, 'candidate_data', return_value=([], 'Names unavailable')):
            response = asyncio.run(app.home(request))
            self.assertIn('Names unavailable', response.body.decode())


if __name__ == '__main__':
    unittest.main()
