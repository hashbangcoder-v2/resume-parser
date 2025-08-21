# LLM Functionality Tests

This directory contains comprehensive tests for the LLM functionality in the resume parser application.

## Test Files

### `test_llm.py`
Main test suite that validates the LLM's ability to process resumes with multimodal input (images + text).

#### Test Classes:

1. **`TestLLMFunctionality`** - Core functionality tests:
   - `test_valid_resume_1_processing()` - Tests processing of first valid resume sample
   - `test_valid_resume_2_processing()` - Tests processing of second valid resume sample  
   - `test_invalid_resume_processing()` - Tests handling of invalid/false resume
   - `test_structured_output_compliance()` - Validates JSON schema compliance
   - `test_multimodal_input_handling()` - Tests image + text processing
   - `test_inference_performance()` - Performance benchmarks (optional)

2. **`TestLLMErrorHandling`** - Error handling scenarios:
   - `test_empty_image_list()` - Tests handling of empty image inputs
   - `test_invalid_job_description()` - Tests handling of invalid job descriptions

## Test Data

The tests use three PDF files from `/test-files/`:
- `sample_resume_1.pdf` - Valid resume sample #1
- `sample_resume_2.pdf` - Valid resume sample #2  
- `sample_false.pdf` - Invalid/false resume for error testing

## Running Tests

### Option 1: Using the Test Runner Script
```bash
cd backend
python scripts/run_llm_tests.py
```

### Option 2: Direct unittest execution
```bash
cd backend
python -m unittest tests.test_llm -v
```

### Option 3: Running specific test classes
```bash
cd backend
python -m unittest tests.test_llm.TestLLMFunctionality -v
python -m unittest tests.test_llm.TestLLMErrorHandling -v
```

### Option 4: Running individual tests
```bash
cd backend
python -m unittest tests.test_llm.TestLLMFunctionality.test_valid_resume_1_processing -v
```

## Expected Behavior

### Valid Resumes (sample_resume_1.pdf, sample_resume_2.pdf)
- Should extract name and email correctly
- Should provide a valid outcome (Shortlisted, Rejected, or Needs Review)
- Should NOT return "Failed" outcome
- Should provide meaningful reasoning

### Invalid Resume (sample_false.pdf)
- Should handle gracefully without crashing
- May return any outcome including "Needs Review" or "Rejected"
- Should provide reasoning for the assessment

### Structured Output
- All responses must conform to `LLMResponse` schema
- Must include: name, email, outcome, reason fields
- Outcome must be a valid `LLMOutcome` enum value
- All fields must be properly typed (strings for name/email/reason)

## Configuration

The tests use the same configuration as `example_llm_infer.py`:
- Model: Qwen/Qwen2.5-Omni-7B
- Temperature: 0.2
- Max tokens: 1024
- Guided decoding with JSON schema enforcement

## Performance Notes

- Individual test inference should complete within 60 seconds
- Performance tests can be skipped by setting `SKIP_PERFORMANCE_TESTS=1`
- Model initialization happens once per test method (not cached across tests)

## Troubleshooting

1. **Missing test files**: Ensure all PDF files exist in `/test-files/` directory
2. **Model loading failures**: Check GPU memory and CUDA availability  
3. **Import errors**: Run from `backend/` directory with proper Python path
4. **Out of memory**: Reduce `gpu_memory_utilization` in test configuration

## Test Output Example

```
🧪 Testing valid resume 1: sample_resume_1.pdf
✅ Valid resume 1 result: Shortlisted - John Doe (john.doe@email.com)
   Reason: Strong technical background with relevant Python experience...

🧪 Testing valid resume 2: sample_resume_2.pdf  
✅ Valid resume 2 result: Needs Review - Jane Smith (jane.smith@email.com)
   Reason: Good qualifications but lacks specific ML framework experience...

🧪 Testing invalid resume: sample_false.pdf
✅ Invalid resume result: Rejected
   Name extracted: 
   Email extracted: 
   Reason: Document does not appear to be a valid resume format...
```
