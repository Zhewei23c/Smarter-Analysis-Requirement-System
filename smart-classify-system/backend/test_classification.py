#!/usr/bin/env python3
"""
Test script for the enhanced requirement classification system
"""

from classifier import classify_requirements, is_functional_requirement

def test_classification():
    """Test the classification system with sample requirements"""
    
    test_cases = [
        # Functional requirements
        ("The system shall allow users to login with username and password", "Functional"),
        ("Users must be able to create, read, update, and delete their profile information", "Functional"),
        ("The system shall generate monthly reports in PDF format", "Functional"),
        ("Users should be able to search for information using keywords", "Functional"),
        ("The system shall validate all user inputs to prevent security vulnerabilities", "Functional"),
        ("Users must be able to export their data in CSV and JSON formats", "Functional"),
        ("The application must allow users to upload and download files", "Functional"),
        ("The system shall provide a dashboard for data visualization", "Functional"),
        ("Users should be able to create and manage user accounts", "Functional"),
        ("The system shall process payment transactions securely", "Functional"),
        
        # Non-functional requirements
        ("The system must respond to user requests within 2 seconds under normal load conditions", "Non-Functional"),
        ("The application must support at least 1000 concurrent users", "Non-Functional"),
        ("The user interface must be accessible and comply with WCAG 2.1 guidelines", "Non-Functional"),
        ("The system shall maintain 99.9% uptime availability", "Non-Functional"),
        ("The application must be compatible with modern web browsers", "Non-Functional"),
        ("The system must log all user activities for audit purposes", "Non-Functional"),
        ("The system shall backup all data daily to prevent data loss", "Non-Functional"),
        ("The application must be scalable to handle increasing user load", "Non-Functional"),
        ("The system shall encrypt all sensitive data in transit and at rest", "Non-Functional"),
        ("The user interface must be responsive and work on mobile devices", "Non-Functional"),
    ]
    
    print("Testing Enhanced Requirement Classification System")
    print("=" * 60)
    
    correct_predictions = 0
    total_predictions = len(test_cases)
    
    for i, (text, expected) in enumerate(test_cases, 1):
        # Test the rule-based classification
        is_functional = is_functional_requirement(text)
        predicted = "Functional" if is_functional else "Non-Functional"
        
        # Check if prediction is correct
        is_correct = predicted == expected
        if is_correct:
            correct_predictions += 1
        
        status = "✓" if is_correct else "✗"
        print(f"{i:2d}. {status} {predicted:15} | {expected:15} | {text[:50]}...")
    
    accuracy = (correct_predictions / total_predictions) * 100
    print("=" * 60)
    print(f"Accuracy: {correct_predictions}/{total_predictions} ({accuracy:.1f}%)")
    
    return accuracy

if __name__ == "__main__":
    test_classification()

