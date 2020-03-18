import React from 'react';
import axios from 'axios';

interface AppState {
  resultTree: any,
  loading: boolean,
}

/**
 * Top level App component.
 */
class App extends React.Component<object, AppState> {
  constructor(props: object) {
    super(props);
    this.state = {
      resultTree: null,
      loading: false,
    }
  }

  componentDidMount() {
    this.setState({ loading: true }, this.getResultTree);
  }

  getResultTree() {
    axios.get("/api/v1/result-tree").then(response => {
      this.setState({ resultTree: response.data, loading: false });
    });
  }

  render() {
    return (
      <div>
        <NavColumn resultTree={this.state.resultTree} />
        <InfoPane resultTree={this.state.resultTree} />
      </div>
    );
  }
}

interface NavProps {
  resultTree: any,
}

interface InfoPaneProps {
  resultTree: any,
}

/**
 * NavColumn component: renders the current navigation selection.
 * @param props Component props
 */
const NavColumn = (props: NavProps) => {
  if (!props.resultTree) {
    return <span>Loading...</span>;
  }

  const childBranches = Object.keys(props.resultTree.child_branches);
  const childLeaves = Object.keys(props.resultTree.child_leaves);
  return (
    <>
      {childBranches.map((entry: string) => <div>{entry + " (branch)"}</div>)}
      {childLeaves.map((entry: string) => <div>{entry + " (leaf)"}</div>)}
    </>
  );
}

/**
 * InfoPane component: renders information on the currently selected testcase (if any)
 * @param props Component props
 */
const InfoPane = (props: InfoPaneProps) => {
  return <span>InfoPane</span>
}

export default App;
