"""
Tests for the Mergington High School Activities API.
Tests follow the AAA (Arrange-Act-Assert) pattern for clarity.
"""
import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_all_activities(self, client):
        """Test retrieving all activities."""
        # Arrange: Nothing to arrange, GET is stateless

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_activity_structure(self, client):
        """Test that each activity has the required fields."""
        # Arrange: Expected field names
        required_fields = ["description", "schedule", "max_participants", "participants"]

        # Act
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]

        # Assert
        for field in required_fields:
            assert field in activity
        assert isinstance(activity["participants"], list)

    def test_participants_list_content(self, client):
        """Test that participants list contains expected data."""
        # Arrange: Expected participants for Chess Club
        expected_participants = ["michael@mergington.edu", "daniel@mergington.edu"]

        # Act
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]

        # Assert
        assert len(chess_club["participants"]) == 2
        for participant in expected_participants:
            assert participant in chess_club["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_successful_signup(self, client):
        """Test successful signup for an activity."""
        # Arrange
        activity = "Chess%20Club"
        new_student = "newstudent@mergington.edu"

        # Act
        response = client.post(f"/activities/{activity}/signup?email={new_student}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert new_student in data["message"]

        # Verify participant was added
        check_response = client.get("/activities")
        activities = check_response.json()
        assert new_student in activities["Chess Club"]["participants"]

    def test_signup_with_special_characters_in_activity_name(self, client):
        """Test signup with activity names containing spaces."""
        # Arrange
        activity = "Basketball%20Team"
        student = "player@mergington.edu"

        # Act
        response = client.post(f"/activities/{activity}/signup?email={student}")

        # Assert
        assert response.status_code == 200

    def test_signup_duplicate_student(self, client):
        """Test that duplicate signups are rejected."""
        # Arrange
        activity = "Chess%20Club"
        existing_student = "michael@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={existing_student}"
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity(self, client):
        """Test signup for an activity that doesn't exist."""
        # Arrange
        nonexistent_activity = "Nonexistent%20Club"
        student = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup?email={student}"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_multiple_students(self, client):
        """Test that multiple different students can sign up."""
        # Arrange
        activity = "Art%20Studio"
        students = ["student1@mergington.edu", "student2@mergington.edu"]

        # Act
        for student in students:
            response = client.post(f"/activities/{activity}/signup?email={student}")
            assert response.status_code == 200

        # Assert
        check_response = client.get("/activities")
        activities = check_response.json()
        for student in students:
            assert student in activities["Art Studio"]["participants"]

    def test_signup_response_message_format(self, client):
        """Test that signup response has correct message format."""
        # Arrange
        activity = "Music%20Ensemble"
        student = "musician@mergington.edu"

        # Act
        response = client.post(f"/activities/{activity}/signup?email={student}")
        data = response.json()

        # Assert
        assert "Signed up" in data["message"]
        assert student in data["message"]
        assert "Music Ensemble" in data["message"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""

    def test_successful_unregister(self, client):
        """Test successful unregister from an activity."""
        # Arrange
        activity = "Chess%20Club"
        participant = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity}/unregister?email={participant}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]

        # Verify participant was removed
        check_response = client.get("/activities")
        activities = check_response.json()
        assert participant not in activities["Chess Club"]["participants"]

    def test_unregister_not_registered_student(self, client):
        """Test unregister for a student not in the activity."""
        # Arrange
        activity = "Chess%20Club"
        nonexistent_student = "nonexistent@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity}/unregister?email={nonexistent_student}"
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]

    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from an activity that doesn't exist."""
        # Arrange
        fake_activity = "Fake%20Club"
        student = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{fake_activity}/unregister?email={student}"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_response_message_format(self, client):
        """Test that unregister response has correct message format."""
        # Arrange
        activity = "Tennis%20Club"
        participant = "alex@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity}/unregister?email={participant}"
        )
        data = response.json()

        # Assert
        assert "Unregistered" in data["message"]
        assert participant in data["message"]
        assert "Tennis Club" in data["message"]

    def test_multiple_unregisters(self, client):
        """Test that only the specified participant is unregistered."""
        # Arrange
        activity = "Chess%20Club"
        target_participant = "michael@mergington.edu"
        other_participant = "daniel@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity}/unregister?email={target_participant}"
        )

        # Assert
        assert response.status_code == 200

        # Verify only target was removed
        check_response = client.get("/activities")
        activities = check_response.json()
        assert target_participant not in activities["Chess Club"]["participants"]
        assert other_participant in activities["Chess Club"]["participants"]


class TestSignupAndUnregisterFlow:
    """Integration tests for signup and unregister workflows."""

    def test_signup_then_unregister(self, client):
        """Test signing up and then unregistering from an activity."""
        # Arrange
        activity = "Debate%20Club"
        student = "testuser@mergington.edu"

        # Act - Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={student}")
        assert signup_response.status_code == 200

        # Assert signup succeeded
        check1 = client.get("/activities")
        assert student in check1.json()["Debate Club"]["participants"]

        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister?email={student}"
        )

        # Assert unregister succeeded
        assert unregister_response.status_code == 200
        check2 = client.get("/activities")
        assert student not in check2.json()["Debate Club"]["participants"]

    def test_signup_unregister_signup_again(self, client):
        """Test that a student can sign up again after unregistering."""
        # Arrange
        activity = "Science%20Lab"
        student = "flaky@mergington.edu"

        # Act - First signup
        response1 = client.post(f"/activities/{activity}/signup?email={student}")

        # Assert first signup successful
        assert response1.status_code == 200

        # Act - Unregister
        response2 = client.delete(f"/activities/{activity}/unregister?email={student}")

        # Assert unregister successful
        assert response2.status_code == 200

        # Act - Second signup (should succeed)
        response3 = client.post(f"/activities/{activity}/signup?email={student}")

        # Assert second signup successful
        assert response3.status_code == 200

        # Verify student is in system
        check = client.get("/activities")
        assert student in check.json()["Science Lab"]["participants"]
