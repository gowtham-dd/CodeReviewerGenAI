from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
import logging
import asyncio  # Add this import at the top

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the state schema
class ReviewState(TypedDict):
    """State maintained throughout the review process"""
    code: str
    language: str
    user_id: str
    review_id: str
    repo_url: str
    deep_analysis: bool
    plagiarism_check: bool
    
    # Agent results
    correctness_result: Dict
    complexity_result: Dict
    readability_result: Dict
    edge_cases_result: Dict
    summarizer_result: Dict
    plagiarism_result: Dict
    
    # Status tracking
    current_agent: str
    errors: List[str]
    start_time: float
    end_time: float


class ReviewGraph:
    """
    LangGraph workflow for multi-agent code review
    Orchestrates all 5 agents in parallel/series as needed
    """
    
    def __init__(self, agents: Dict):
        self.agents = agents
        self.graph = self._build_graph()
    

# In the _build_graph method, modify the flow:

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow with delays"""
    
    # Initialize the graph
        workflow = StateGraph(ReviewState)
    
    # Add nodes for each agent
        workflow.add_node("correctness", self._run_correctness)
        workflow.add_node("delay_1", self._delay_2_seconds)  # Add delay node
        workflow.add_node("complexity", self._run_complexity)
        workflow.add_node("delay_2", self._delay_2_seconds)  # Add delay node
        workflow.add_node("readability", self._run_readability)
        workflow.add_node("delay_3", self._delay_2_seconds)  # Add delay node
        workflow.add_node("edge_cases", self._run_edge_cases)
        workflow.add_node("delay_4", self._delay_2_seconds)  # Add delay node
        workflow.add_node("plagiarism", self._run_plagiarism)
        workflow.add_node("delay_5", self._delay_2_seconds)  # Add delay node
        workflow.add_node("summarizer", self._run_summarizer)
        workflow.add_node("error_handler", self._handle_errors)
    
    # Define the flow with delays
        workflow.set_entry_point("correctness")
    
    # Add delays between each agent
        workflow.add_edge("correctness", "delay_1")
        workflow.add_edge("delay_1", "complexity")
        workflow.add_edge("complexity", "delay_2")
        workflow.add_edge("delay_2", "readability")
        workflow.add_edge("readability", "delay_3")
        workflow.add_edge("delay_3", "edge_cases")
    
    # Conditional branch for plagiarism check
        workflow.add_conditional_edges(
        "edge_cases",
            self._should_check_plagiarism,
            {
            True: "delay_4",
            False: "delay_5"
            }
        )
    
        workflow.add_edge("delay_4", "plagiarism")
        workflow.add_edge("plagiarism", "delay_5")
        workflow.add_edge("delay_5", "summarizer")
        workflow.add_edge("summarizer", END)
    
        return workflow.compile()

# Add this new method to the ReviewGraph class
    async def _delay_2_seconds(self, state: ReviewState) -> ReviewState:
        """Add a 2-second delay between API calls to avoid rate limits"""
        logger.info(f"⏱️  Delaying for 2 seconds before next agent...")
        await asyncio.sleep(2)
        return state

    async def _run_correctness(self, state: ReviewState) -> ReviewState:
        """Run correctness agent"""
        logger.info("Running correctness agent")
        state["current_agent"] = "correctness"
        
        try:
            result = await self.agents["correctness"].review(
                state["code"],
                state["language"]
            )
            state["correctness_result"] = result
        except Exception as e:
            logger.error(f"Correctness agent error: {e}")
            state["errors"].append(f"Correctness: {str(e)}")
        
        return state
    
    async def _run_complexity(self, state: ReviewState) -> ReviewState:
        """Run complexity agent"""
        logger.info("Running complexity agent")
        state["current_agent"] = "complexity"
        
        try:
            result = await self.agents["complexity"].analyze(
                state["code"],
                state["language"]
            )
            state["complexity_result"] = result
        except Exception as e:
            logger.error(f"Complexity agent error: {e}")
            state["errors"].append(f"Complexity: {str(e)}")
        
        return state
    
    async def _run_readability(self, state: ReviewState) -> ReviewState:
        """Run readability agent"""
        logger.info("Running readability agent")
        state["current_agent"] = "readability"
        
        try:
            result = await self.agents["readability"].review(
                state["code"],
                state["language"],
                state["user_id"]
            )
            state["readability_result"] = result
        except Exception as e:
            logger.error(f"Readability agent error: {e}")
            state["errors"].append(f"Readability: {str(e)}")
        
        return state
    
    async def _run_edge_cases(self, state: ReviewState) -> ReviewState:
        """Run edge cases agent"""
        logger.info("Running edge cases agent")
        state["current_agent"] = "edge_cases"
        
        try:
            result = await self.agents["edge_cases"].generate_cases(
                state["code"],
                state["language"]
            )
            state["edge_cases_result"] = result
        except Exception as e:
            logger.error(f"Edge cases agent error: {e}")
            state["errors"].append(f"Edge Cases: {str(e)}")
        
        return state
    
    async def _run_plagiarism(self, state: ReviewState) -> ReviewState:
        """Run plagiarism detector"""
        logger.info("Running plagiarism check")
        state["current_agent"] = "plagiarism"
        
        try:
            result = self.agents["plagiarism"].detect(state["code"])
            state["plagiarism_result"] = result
        except Exception as e:
            logger.error(f"Plagiarism detector error: {e}")
            state["errors"].append(f"Plagiarism: {str(e)}")
        
        return state
    
    async def _run_summarizer(self, state: ReviewState) -> ReviewState:
        """Run summarizer agent"""
        logger.info("Running summarizer agent")
        state["current_agent"] = "summarizer"
        
        try:
            result = await self.agents["summarizer"].summarize(
                state["code"],
                state["language"],
                state.get("correctness_result", {}),
                state.get("complexity_result", {}),
                state.get("readability_result", {}),
                state.get("edge_cases_result", {}),
                state["user_id"]
            )
            state["summarizer_result"] = result
        except Exception as e:
            logger.error(f"Summarizer agent error: {e}")
            state["errors"].append(f"Summarizer: {str(e)}")
        
        return state
    
    def _should_check_plagiarism(self, state: ReviewState) -> bool:
        """Determine if plagiarism check should run"""
        return state.get("plagiarism_check", False)
    
    def _handle_errors(self, state: ReviewState) -> ReviewState:
        """Handle any errors in the workflow"""
        if state["errors"]:
            logger.warning(f"Errors in review: {state['errors']}")
            # Could add recovery logic here
        return state
    
    async def run(self, initial_state: ReviewState) -> ReviewState:
        """
        Run the complete review workflow
        """
        import time
        state = initial_state
        state["start_time"] = time.time()
        state["errors"] = []
        
        try:
            # Run the graph
            result = await self.graph.ainvoke(state)
            result["end_time"] = time.time()
            result["duration"] = result["end_time"] - result["start_time"]
            
            return result
        except Exception as e:
            logger.error(f"Graph execution error: {e}")
            state["errors"].append(f"Graph: {str(e)}")
            return state