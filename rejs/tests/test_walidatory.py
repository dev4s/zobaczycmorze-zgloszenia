from django.core.exceptions import ValidationError
from django.test import TestCase

from rejs.walidatory import validate_pesel


class ValidatePeselTest(TestCase):
	"""Testy funkcji walidacji PESEL."""

	def test_valid_pesel(self):
		"""Test poprawnego numeru PESEL."""
		# 90021401384 - poprawny PESEL (suma kontrolna = 0 mod 10)
		result = validate_pesel("90021401384")
		self.assertEqual(result, "90021401384")

	def test_valid_pesel_with_spaces(self):
		"""Test PESEL ze spacjami - powinny być usunięte."""
		result = validate_pesel("900 214 013 84")
		self.assertEqual(result, "90021401384")

	def test_valid_pesel_with_dashes(self):
		"""Test PESEL z myślnikami - powinny być usunięte."""
		result = validate_pesel("900-214-013-84")
		self.assertEqual(result, "90021401384")

	def test_empty_pesel(self):
		"""Test pustego PESEL."""
		with self.assertRaises(ValidationError) as context:
			validate_pesel("")
		self.assertIn("wymagany", str(context.exception))

	def test_pesel_too_short(self):
		"""Test za krótkiego PESEL."""
		with self.assertRaises(ValidationError) as context:
			validate_pesel("1234567890")  # 10 cyfr
		self.assertIn("11 cyfr", str(context.exception))

	def test_pesel_too_long(self):
		"""Test za długiego PESEL."""
		with self.assertRaises(ValidationError) as context:
			validate_pesel("123456789012")  # 12 cyfr
		self.assertIn("11 cyfr", str(context.exception))

	def test_pesel_with_letters(self):
		"""Test PESEL z literami."""
		with self.assertRaises(ValidationError) as context:
			validate_pesel("9002140138A")
		self.assertIn("tylko cyfry", str(context.exception))

	def test_pesel_invalid_checksum(self):
		"""Test PESEL z błędną sumą kontrolną."""
		with self.assertRaises(ValidationError) as context:
			validate_pesel("90021401385")  # ostatnia cyfra zmieniona (4->5)
		self.assertIn("suma kontrolna", str(context.exception))

	def test_pesel_all_zeros(self):
		"""Test PESEL składającego się z samych zer."""
		# 00000000000 ma sumę kontrolną 0, więc jest technicznie poprawny
		result = validate_pesel("00000000000")
		self.assertEqual(result, "00000000000")
