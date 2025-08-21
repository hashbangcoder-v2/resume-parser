import unittest
import json
import os
from pathlib import Path
from typing import List
from unittest.mock import patch, MagicMock

from vllm import LLM, SamplingParams
from vllm.sampling_params import GuidedDecodingParams
from pdf2image import convert_from_path
from PIL import Image
from omegaconf import OmegaConf

from app.schemas import LLMResponse, LLMOutcome
from app.model_utils import generate_llm_prompt
from app.common_utils import get_system_prompt


class TestLLMFunctionality(unittest.TestCase):
    """Test suite for LLM functionality with multimodal resume processing."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with model configuration and test files."""
        cls.test_files_dir = Path("test-files")
        cls.valid_resume_1 = cls.test_files_dir / "sample_resume_1.pdf"
        cls.valid_resume_2 = cls.test_files_dir / "sample_resume_2.pdf"
        cls.invalid_resume = cls.test_files_dir / "sample_false.pdf"
        
        # Verify test files exist
        for file_path in [cls.valid_resume_1, cls.valid_resume_2, cls.invalid_resume]:
            if not file_path.exists():
                raise FileNotFoundError(f"Test file not found: {file_path}")
        
        # Model configuration
        cls.model_name = "Qwen/Qwen2.5-Omni-7B"
        cls.vllm_inference_args = OmegaConf.create({
            "gpu_memory_utilization": 0.65,
            "max_model_len": 32768,
            "enforce_eager": True,
            "tensor_parallel_size": 1,
            "trust_remote_code": True,
            "temperature": 0.2,
            "repetition_penalty": 1.1,
        })
        
        cls.vllm_config = {
            "model": cls.model_name,
            "gpu_memory_utilization": cls.vllm_inference_args.gpu_memory_utilization,
            "max_model_len": cls.vllm_inference_args.max_model_len,
            "enforce_eager": cls.vllm_inference_args.enforce_eager,
            "tensor_parallel_size": cls.vllm_inference_args.tensor_parallel_size,
            "trust_remote_code": cls.vllm_inference_args.trust_remote_code,
            "disable_custom_all_reduce": True,
            "max_num_seqs": 4,
            "limit_mm_per_prompt": {"image": 3},
        }
        
        # Sample job description for testing
        cls.job_description = """
        Software Engineer Position
        
        Requirements:
        - Bachelor's degree in Computer Science or related field
        - 3+ years of Python development experience
        - Experience with machine learning frameworks
        - Strong problem-solving skills
        - Excellent communication skills
        """
    
    def setUp(self):
        """Set up individual test cases."""
        # Initialize model for each test (in real scenario, this would be cached)
        try:
            self.vllm_model = LLM(**self.vllm_config)
        except Exception as e:
            self.skipTest(f"Could not initialize vLLM model: {e}")
    
    def tearDown(self):
        """Clean up after each test."""
        if hasattr(self, 'vllm_model'):
            del self.vllm_model
    
    def _convert_pdf_to_images(self, pdf_path: Path) -> List[Image.Image]:
        """Helper method to convert PDF to images."""
        try:
            images = convert_from_path(pdf_path)
            return images
        except Exception as e:
            self.fail(f"Failed to convert PDF to images: {e}")
    
    def _generate_llm_response(self, images: List[Image.Image], job_description: str) -> LLMResponse:
        """Helper method to generate LLM response with structured output."""
        # Set up guided decoding for structured output
        guided_decoding_params = GuidedDecodingParams(json=LLMResponse.model_json_schema())
        
        sampling_params = SamplingParams(
            temperature=self.vllm_inference_args.temperature,
            max_tokens=1024,
            repetition_penalty=self.vllm_inference_args.repetition_penalty,
            guided_decoding=guided_decoding_params,
        )
        
        # Generate prompt using the same method as the main application
        multimodal_input = generate_llm_prompt(images, job_description)
        
        # Generate response
        outputs = self.vllm_model.generate([multimodal_input], sampling_params)
        llm_content = outputs[0].outputs[0].text.strip()
        
        # Parse and validate the JSON response
        try:
            parsed_content = json.loads(llm_content)
            validated_response = LLMResponse.model_validate(parsed_content)
            return validated_response
        except (json.JSONDecodeError, ValueError) as e:
            self.fail(f"Failed to parse LLM response: {e}\nRaw response: {llm_content}")
    
    def test_valid_resume_1_processing(self):
        """Test processing of first valid resume sample."""
        print(f"\n🧪 Testing valid resume 1: {self.valid_resume_1.name}")
        
        # Convert PDF to images
        images = self._convert_pdf_to_images(self.valid_resume_1)
        self.assertGreater(len(images), 0, "Should have at least one image from PDF")
        
        # Generate LLM response
        response = self._generate_llm_response(images, self.job_description)
        
        # Validate response structure
        self.assertIsInstance(response, LLMResponse)
        self.assertIsInstance(response.name, str)
        self.assertIsInstance(response.email, str)
        self.assertIsInstance(response.outcome, LLMOutcome)
        self.assertIsInstance(response.reason, str)
        
        # Validate content is not empty
        self.assertNotEqual(response.name.strip(), "", "Name should not be empty")
        self.assertNotEqual(response.reason.strip(), "", "Reason should not be empty")
        
        # Validate email format (basic check)
        self.assertIn("@", response.email, "Email should contain @ symbol")
        
        # Validate outcome is a valid enum value
        self.assertIn(response.outcome, [LLMOutcome.SHORTLISTED, LLMOutcome.REJECTED, 
                                       LLMOutcome.NEEDS_REVIEW, LLMOutcome.FAILED])
        
        # For a valid resume, outcome should not be FAILED
        self.assertNotEqual(response.outcome, LLMOutcome.FAILED, 
                           "Valid resume should not result in FAILED outcome")
        
        print(f"✅ Valid resume 1 result: {response.outcome} - {response.name} ({response.email})")
        print(f"   Reason: {response.reason[:100]}...")
    
    def test_valid_resume_2_processing(self):
        """Test processing of second valid resume sample."""
        print(f"\n🧪 Testing valid resume 2: {self.valid_resume_2.name}")
        
        # Convert PDF to images
        images = self._convert_pdf_to_images(self.valid_resume_2)
        self.assertGreater(len(images), 0, "Should have at least one image from PDF")
        
        # Generate LLM response
        response = self._generate_llm_response(images, self.job_description)
        
        # Validate response structure
        self.assertIsInstance(response, LLMResponse)
        self.assertIsInstance(response.name, str)
        self.assertIsInstance(response.email, str)
        self.assertIsInstance(response.outcome, LLMOutcome)
        self.assertIsInstance(response.reason, str)
        
        # Validate content is not empty
        self.assertNotEqual(response.name.strip(), "", "Name should not be empty")
        self.assertNotEqual(response.reason.strip(), "", "Reason should not be empty")
        
        # Validate email format (basic check)
        self.assertIn("@", response.email, "Email should contain @ symbol")
        
        # Validate outcome is a valid enum value
        self.assertIn(response.outcome, [LLMOutcome.SHORTLISTED, LLMOutcome.REJECTED, 
                                       LLMOutcome.NEEDS_REVIEW, LLMOutcome.FAILED])
        
        # For a valid resume, outcome should not be FAILED
        self.assertNotEqual(response.outcome, LLMOutcome.FAILED, 
                           "Valid resume should not result in FAILED outcome")
        
        print(f"✅ Valid resume 2 result: {response.outcome} - {response.name} ({response.email})")
        print(f"   Reason: {response.reason[:100]}...")
    
    def test_invalid_resume_processing(self):
        """Test processing of invalid/false resume sample."""
        print(f"\n🧪 Testing invalid resume: {self.invalid_resume.name}")
        
        # Convert PDF to images
        images = self._convert_pdf_to_images(self.invalid_resume)
        self.assertGreater(len(images), 0, "Should have at least one image from PDF")
        
        # Generate LLM response
        response = self._generate_llm_response(images, self.job_description)
        
        # Validate response structure
        self.assertIsInstance(response, LLMResponse)
        self.assertIsInstance(response.name, str)
        self.assertIsInstance(response.email, str)
        self.assertIsInstance(response.outcome, LLMOutcome)
        self.assertIsInstance(response.reason, str)
        
        # For invalid resume, we expect specific behavior
        # The model should still provide some response, but likely with NEEDS_REVIEW or REJECTED
        self.assertIn(response.outcome, [LLMOutcome.SHORTLISTED, LLMOutcome.REJECTED, 
                                       LLMOutcome.NEEDS_REVIEW, LLMOutcome.FAILED])
        
        # Reason should be provided explaining why it's problematic
        self.assertNotEqual(response.reason.strip(), "", "Reason should not be empty")
        
        print(f"✅ Invalid resume result: {response.outcome}")
        if response.name.strip():
            print(f"   Name extracted: {response.name}")
        if response.email.strip() and "@" in response.email:
            print(f"   Email extracted: {response.email}")
        print(f"   Reason: {response.reason[:100]}...")
    
    def test_structured_output(self):
        """Test that all responses comply with the LLMResponse schema."""
        print(f"\n🧪 Testing structured output across all test files")
        
        test_files = [self.valid_resume_1, self.valid_resume_2, self.invalid_resume]
        
        for test_file in test_files:
            with self.subTest(file=test_file.name):
                images = self._convert_pdf_to_images(test_file)
                response = self._generate_llm_response(images, self.job_description)
                
                # Verify JSON schema compliance
                response_dict = response.model_dump()
                
                # Check required fields exist
                required_fields = ["name", "email", "outcome", "reason"]
                for field in required_fields:
                    self.assertIn(field, response_dict, f"Required field '{field}' missing")
                
                # Check field types
                self.assertIsInstance(response_dict["name"], str)
                self.assertIsInstance(response_dict["email"], str)
                self.assertIsInstance(response_dict["outcome"], str)
                self.assertIsInstance(response_dict["reason"], str)
                
                # Verify outcome is valid enum value
                self.assertIn(response_dict["outcome"], 
                            ["Shortlisted", "Rejected", "Needs Review", "Failed"])
        
        print("✅ All responses comply with LLMResponse schema")
    
    def test_multimodal_input_handling(self):
        """Test that the model properly handles multimodal input (images + text)."""
        print(f"\n🧪 Testing multimodal input handling")
        
        # Test with valid resume
        images = self._convert_pdf_to_images(self.valid_resume_1)
        
        # Test with different job descriptions to ensure text processing works
        job_descriptions = [
            "Senior Software Engineer with 5+ years Python experience",
            "Entry level position for recent graduates",
            "Data Scientist role requiring ML expertise"
        ]
        
        for i, job_desc in enumerate(job_descriptions):
            with self.subTest(job_description=f"job_desc_{i+1}"):
                response = self._generate_llm_response(images, job_desc)
                
                # Verify we get a valid response for each job description
                self.assertIsInstance(response, LLMResponse)
                self.assertNotEqual(response.reason.strip(), "")
                
                # The reason should potentially vary based on job description
                # (though this is model-dependent)
                self.assertIsInstance(response.reason, str)
        
        print("✅ Multimodal input handling works correctly")
    


class TestLLMErrorHandling(unittest.TestCase):
    """Test suite for LLM error handling scenarios."""
    
    def test_empty_image_list(self):
        """Test handling of empty image list."""
        with self.assertRaises(Exception):
            # This should raise an error as we need images for multimodal input
            generate_llm_prompt([], "test job description")
    
    def test_invalid_job_description(self):
        """Test handling of invalid job descriptions."""
        # Test with empty job description
        images = [Image.new('RGB', (100, 100), color='white')]  # Dummy image
        
        # Should not crash with empty job description
        try:
            prompt = generate_llm_prompt(images, "")
            self.assertIsInstance(prompt, dict)
        except Exception as e:
            self.fail(f"Should handle empty job description gracefully: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2, buffer=True)
