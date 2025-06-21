"""
Task: Implement Calculator Functionality
Description: Write Python code to handle user input, perform calculations, and display results. Ensure all four basic arithmetic operations are implemented.
Generated: 2025-06-21 13:20:05
"""

import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO)

class Calculator:
    """
    A basic calculator class with methods for addition, subtraction, multiplication, division, exponentiation, square root, absolute value, and factorial.
    """

    def add(self, num1, num2):
        """
        Adds two numbers.

        Args:
            num1 (float): The first number.
            num2 (float): The second number.

        Returns:
            float: The sum of the two numbers.
        """
        logging.info("Performing addition")
        try:
            result = num1 + num2
            return result
        except TypeError:
            logging.error("Invalid input type. Please enter numbers only.")
            return None

    def subtract(self, num1, num2):
        """
        Subtracts the second number from the first.

        Args:
            num1 (float): The first number.
            num2 (float): The second number.

        Returns:
            float: The difference between the two numbers.
        """
        logging.info("Performing subtraction")
        try:
            result = num1 - num2
            return result
        except TypeError:
            logging.error("Invalid input type. Please enter numbers only.")
            return None

    def multiply(self, num1, num2):
        """
        Multiplies two numbers.

        Args:
            num1 (float): The first number.
            num2 (float): The second number.

        Returns:
            float: The product of the two numbers.
        """
        logging.info("Performing multiplication")
        try:
            result = num1 * num2
            return result
        except TypeError:
            logging.error("Invalid input type. Please enter numbers only.")
            return None

    def divide(self, num1, num2):
        """
        Divides the first number by the second.

        Args:
            num1 (float): The dividend.
            num2 (float): The divisor.

        Returns:
            float: The quotient of the two numbers.
        """
        logging.info("Performing division")
        try:
            if num2 == 0:
                raise ZeroDivisionError
            result = num1 / num2
            return result
        except TypeError:
            logging.error("Invalid input type. Please enter numbers only.")
            return None
        except ZeroDivisionError:
            logging.error("Cannot divide by zero")
            return None

    def exponentiate(self, base, exponent):
        """
        Calculates the power of a number.

        Args:
            base (float): The base.
            exponent (float): The exponent.

        Returns:
            float: The result of raising the base to the power of the exponent.
        """
        logging.info("Performing exponentiation")
        try:
            result = base ** exponent
            return result
        except TypeError:
            logging.error("Invalid input type. Please enter numbers only.")
            return None

    def square_root(self, num):
        """
        Calculates the square root of a number.

        Args:
            num (float): The number to calculate the square root of.

        Returns:
            float: The square root of the number.
        """
        logging.info("Calculating square root")
        try:
            if num < 0:
                raise ValueError
            result = num ** 0.5
            return result
        except TypeError:
            logging.error("Invalid input type. Please enter a number.")
            return None
        except ValueError:
            logging.error("Cannot calculate square root of negative number")
            return None

    def absolute_value(self, num):
        """
        Calculates the absolute value of a number.

        Args:
            num (float): The number to calculate the absolute value of.

        Returns:
            float: The absolute value of the number.
        """
        logging.info("Calculating absolute value")
        try:
            result = abs(num)
            return result
        except TypeError:
            logging.error("Invalid input type. Please enter a number.")
            return None

    def factorial(self, num):
        """
        Calculates the factorial of an integer.

        Args:
            num (int): The number to calculate the factorial of.

        Returns:
            int: The factorial of the number.
        """
        logging.info("Calculating factorial")
        try:
            if not isinstance(num, int) or num < 0:
                raise TypeError
            result = 1
            for i in range(1, num + 1):
                result *= i
            return result
        except TypeError:
            logging.error("Invalid input type. Please enter an integer.")
            return None

# Example usage:
if __name__ == "__main__":
    calc = Calculator()
    print(calc.add(10, 5))  # Output: 15
    print(calc.subtract(10, 5))  # Output: 5
    print(calc.multiply(10, 5))  # Output: 50
    print(calc.divide(10, 2))  # Output: 5.0
    print(calc.exponentiate(2, 3))  # Output: 8
    print(calc.square_root(16))  # Output: 4.0
    print(calc.absolute_value(-5))  # Output: 5
    print(calc.factorial(5))  # Output: 120