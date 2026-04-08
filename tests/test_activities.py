import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities"""
        # Arrange
        expected_activity_count = 9
        expected_activities = ["Chess Club", "Programming Class", "Basketball Team"]
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        assert response.status_code == 200
        assert len(activities) == expected_activity_count
        for activity in expected_activities:
            assert activity in activities
    
    def test_get_activities_returns_participant_count(self, client, reset_activities):
        """Test that activities include participant information"""
        # Arrange
        expected_chess_participants = ["michael@mergington.edu", "daniel@mergington.edu"]
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        chess_club = activities["Chess Club"]
        
        # Assert
        assert response.status_code == 200
        assert chess_club["participants"] == expected_chess_participants
        assert chess_club["max_participants"] == 12


class TestSignUp:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant(self, client, reset_activities):
        """Test signing up a new participant for an activity"""
        # Arrange
        activity_name = "Basketball Team"
        new_email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={new_email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert new_email in response.json()["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        basketball = activities_response.json()[activity_name]
        assert new_email in basketball["participants"]
    
    def test_signup_duplicate_participant_returns_400(self, client, reset_activities):
        """Test that duplicate signups are rejected with 400 error"""
        # Arrange
        activity_name = "Chess Club"
        duplicate_email = "duplicate@mergington.edu"
        
        # Act - First signup
        client.post(f"/activities/{activity_name}/signup?email={duplicate_email}")
        
        # Act - Second signup with same email
        response = client.post(
            f"/activities/{activity_name}/signup?email={duplicate_email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test signup for non-existent activity returns 404 error"""
        # Arrange
        nonexistent_activity = "Nonexistent Club"
        student_email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup?email={student_email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_signup_updates_availability(self, client, reset_activities):
        """Test that signup correctly updates available spots"""
        # Arrange
        activity_name = "Soccer Club"
        initial_max = 22
        student1 = "student1@mergington.edu"
        student2 = "student2@mergington.edu"
        
        # Act - Sign up first student
        client.post(f"/activities/{activity_name}/signup?email={student1}")
        
        # Act - Sign up second student
        client.post(f"/activities/{activity_name}/signup?email={student2}")
        
        # Assert
        response = client.get("/activities")
        activity = response.json()[activity_name]
        current_spots = initial_max - len(activity["participants"])
        
        assert len(activity["participants"]) == 2
        assert current_spots == 20


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_participant_succeeds(self, client, reset_activities):
        """Test unregistering an existing participant succeeds"""
        # Arrange
        activity_name = "Chess Club"
        participant_email = "michael@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={participant_email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert participant_email in response.json()["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert participant_email not in participants
    
    def test_unregister_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test unregistering from non-existent activity returns 404"""
        # Arrange
        nonexistent_activity = "Nonexistent Club"
        student_email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{nonexistent_activity}/unregister?email={student_email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_unregister_nonexistent_participant_returns_400(self, client, reset_activities):
        """Test unregistering a participant not signed up returns 400"""
        # Arrange
        activity_name = "Basketball Team"
        not_registered_email = "notregistered@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={not_registered_email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_unregister_participant_not_in_activity_returns_400(self, client, reset_activities):
        """Test unregistering a participant from wrong activity returns 400"""
        # Arrange
        activity_name = "Basketball Team"
        participant_not_in_activity = "michael@mergington.edu"  # In Chess Club, not Basketball
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={participant_not_in_activity}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]


class TestSignupAndUnregister:
    """Integration tests for signup and unregister workflows"""
    
    def test_full_lifecycle_signup_then_unregister(self, client, reset_activities):
        """Test complete lifecycle: signup, verify, unregister, verify removal"""
        # Arrange
        email = "integrationtest@mergington.edu"
        activity = "Debate Club"
        
        # Act - Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert - Signup succeeded
        assert signup_response.status_code == 200
        activities = client.get("/activities").json()
        assert email in activities[activity]["participants"]
        
        # Act - Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Assert - Unregister succeeded
        assert unregister_response.status_code == 200
        activities = client.get("/activities").json()
        assert email not in activities[activity]["participants"]
    
    def test_multiple_students_signup_and_partial_unregister(self, client, reset_activities):
        """Test multiple students signing up with partial unregistering"""
        # Arrange
        activity = "Science Club"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        removing_email = emails[1]
        
        # Act - Sign up all students
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Assert - All signed up
        activities = client.get("/activities").json()
        assert len(activities[activity]["participants"]) == 3
        
        # Act - Unregister one student
        unregister_response = client.delete(
            f"/activities/{activity}/unregister?email={removing_email}"
        )
        
        # Assert - One removed, two remain
        assert unregister_response.status_code == 200
        activities = client.get("/activities").json()
        assert len(activities[activity]["participants"]) == 2
        assert removing_email not in activities[activity]["participants"]
        assert emails[0] in activities[activity]["participants"]
        assert emails[2] in activities[activity]["participants"]
    
    def test_signup_same_student_after_unregister(self, client, reset_activities):
        """Test that a student can sign up again after unregistering"""
        # Arrange
        email = "flexible@mergington.edu"
        activity = "Drama Club"
        
        # Act - Sign up
        signup1 = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert - First signup succeeded
        assert signup1.status_code == 200
        
        # Act - Unregister
        unregister = client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Assert - Unregister succeeded
        assert unregister.status_code == 200
        
        # Act - Sign up again
        signup2 = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert - Second signup succeeded
        assert signup2.status_code == 200
        activities = client.get("/activities").json()
        assert email in activities[activity]["participants"]
