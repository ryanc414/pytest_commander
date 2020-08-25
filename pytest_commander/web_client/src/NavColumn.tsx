/**
 * Navigation column component and its subcomponents. Used to control navigation
 * from a current selected branch node down to its child nodes.
 */
import React from 'react';
import _ from 'lodash';
import { ListGroup, ListGroupItem } from 'reactstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlay, faRedo, faToggleOn, faToggleOff } from '@fortawesome/free-solid-svg-icons';
import { Link } from "react-router-dom";
import { StyleSheet, css } from "aphrodite";

import { LIGHT_GREY, MEDIUM_GREY, COLWIDTH, BranchNode, LeafNode } from "./Common";

interface NavColumnProps {
  childBranches: { [key: string]: BranchNode },
  childLeaves: { [key: string]: LeafNode },
  selectedLeafID: string | null,
  selection: Array<string>,
  handleTestRun: (nodeid: string) => void,
  handleEnvToggle: (nodeid: string, start: boolean) => void,
}

/**
 * NavColumn component: renders the current navigation selection.
 * @param props Component props
 */
export const NavColumn = (props: NavColumnProps) => {
  if (_.isEmpty(props.childBranches) && _.isEmpty(props.childLeaves)) {
    return <div className={css(styles.navColumn)} />;
  }

  return (
    <div className={css(styles.navColumn)}>
      <ListGroup>
        <NavEntries
          childBranches={props.childBranches}
          childLeaves={props.childLeaves}
          selection={props.selection}
          selectedLeafID={props.selectedLeafID}
          handleTestRun={props.handleTestRun}
          handleEnvToggle={props.handleEnvToggle}
        />
      </ListGroup>
    </div>
  );
};

interface NavEntriesProps {
  childBranches: { [key: string]: BranchNode },
  childLeaves: { [key: string]: LeafNode },
  selection: Array<string>,
  selectedLeafID: string | null,
  handleTestRun: (nodeid: string) => void,
  handleEnvToggle: (nodeid: string, start: boolean) => void,
}

interface NodeIDInfo {
  shortID: string,
  branch: boolean,
}

/**
 * Render entries in the nav column for branch nodes that are children of the
 * currently selected node.
 * @param props Render props
 */
const NavEntries = (props: NavEntriesProps) => {
  const childIDs = Object.keys(props.childBranches).map(
    shortID => ({shortID: shortID, branch: true})
  ).concat(
    Object.keys(props.childLeaves).map(
      shortID => ({shortID: shortID, branch: false})
    )
  ).sort((a: NodeIDInfo, b: NodeIDInfo) => (a.shortID.localeCompare(b.shortID)))

  return (
    <>
      {
        childIDs.map(
          (nodeInfo: NodeIDInfo) => {
            if (nodeInfo.branch) {
              const childNode = props.childBranches[nodeInfo.shortID]
              return <BranchEntry
                node={childNode}
                selection={props.selection}
                handleTestRun={props.handleTestRun}
                handleEnvToggle={props.handleEnvToggle}
              />
            } else {
              const childNode = props.childLeaves[nodeInfo.shortID]
              return <LeafEntry
                node={childNode}
                selectedLeafID={props.selectedLeafID}
                handleTestRun={props.handleTestRun}
              />
            }
          }
        )
      }
    </>
  );
};

interface BranchEntryProps {
  node: BranchNode,
  selection: Array<string>,
  handleTestRun: (nodeid: string) => void,
  handleEnvToggle: (nodeid: string, start: boolean) => void,
}

const BranchEntry = (props: BranchEntryProps) => {
  const linkAddr = "/" + props.selection
    .concat([props.node.short_id])
    .map(encodeURIComponent)
    .join("/");

  return (
    <ListGroupItem
      key={props.node.short_id}
      className={
        css(
          getNavEntryStyle(props.node.status),
          styles.navEntryCommon,
        )
      }
    >
      <span className={css(styles.navLabel)}>
        <Link
          to={linkAddr}
        >
          {props.node.short_id}
        </Link>
      </span>
      <BranchEntryButtons
        node={props.node}
        handleTestRun={props.handleTestRun}
        handleEnvToggle={props.handleEnvToggle}
      />
    </ListGroupItem>
  );
};

interface BranchEntryButtonsProps {
  node: BranchNode,
  handleTestRun: (nodeid: string) => void,
  handleEnvToggle: (nodeid: string, start: boolean) => void,
}

const BranchEntryButtons: React.FunctionComponent<BranchEntryButtonsProps> = props => {
  if (props.node.environment_state === "inactive") {
    return (
      <NavEntryIcon
        nodeid={props.node.nodeid}
        status={props.node.status}
        handleTestRun={props.handleTestRun}
      />
    );
  }

  return (
    <span className={css(styles.buttonsContainer, styles.navEntryCommon)}>
      <EnvironmentIcon
        envStatus={props.node.environment_state}
        handleEnvToggle={props.handleEnvToggle}
        nodeid={props.node.nodeid}
      />
      <NavEntryIcon
        nodeid={props.node.nodeid}
        status={props.node.status}
        handleTestRun={props.handleTestRun}
      />
    </span>
  );
};

interface LeafEntryProps {
  node: LeafNode
  selectedLeafID: string | null,
  handleTestRun: (nodeid: string) => void,
}

/**
 * Render entries in the navigation column for child leaves of the currently
 * selected node.
 * @param props Render props
 */
const LeafEntry = (props: LeafEntryProps) => {
  const shortID = props.node.short_id
  const label = (shortID === props.selectedLeafID) ?
    shortID :
    (
      <Link
        to={`?selectedLeaf=${encodeURIComponent(shortID)}`}
      >
        {shortID}
      </Link>
    );

  return (
    <ListGroupItem
      key={shortID}
      className={
        css(
          getNavEntryStyle(
            props.node.status
          ),
          styles.navEntryCommon,
        )
      }
    >
      <span className={css(styles.navLabel)}>{label}</span>
      <NavEntryIcon
        nodeid={props.node.nodeid}
        status={props.node.status}
        handleTestRun={props.handleTestRun}
      />
    </ListGroupItem>
  );
};

interface NavEntryIconProps {
  nodeid: string,
  status: string,
  handleTestRun: (nodeid: string) => void,
}

const NavEntryIcon = (props: NavEntryIconProps) => {
  switch (props.status) {
    case "running":
      return (
        <FontAwesomeIcon
          icon={faRedo}
          className={css(styles.inactiveButton)}
          size="lg"
          spin
        />
      );

    default:
      return (
        <FontAwesomeIcon
          icon={faPlay}
          onClick={(e: React.MouseEvent) => {
            e.stopPropagation();
            props.handleTestRun(props.nodeid);
          }}
          className={css(styles.runButton)}
          size="lg"
        />
      );
  }
};

interface EnvironmentIconProps {
  envStatus: string,
  nodeid: string,
  handleEnvToggle: (nodeid: string, start: boolean) => void,
}

const EnvironmentIcon: React.FunctionComponent<EnvironmentIconProps> = (props)=> {
  switch (props.envStatus) {
    case "stopped":
      return (
        <FontAwesomeIcon
          icon={faToggleOff}
          className={css(styles.runButton)}
          onClick={(e: React.MouseEvent) => {
            e.stopPropagation();
            props.handleEnvToggle(props.nodeid, true);
          }}
          size="lg"
        />
      );

    case "started":
      return (
        <FontAwesomeIcon
          icon={faToggleOn}
          className={css(styles.runButton)}
          onClick={(e: React.MouseEvent) => {
            e.stopPropagation();
            props.handleEnvToggle(props.nodeid, false);
          }}
          size="lg"
        />
      );

    case "stopping":
      return (
        <FontAwesomeIcon
          icon={faToggleOn}
          className={css(styles.inactiveButton)}
          size="lg"
        />
      );

    default:
      throw new Error("unexpected environment status " + props.envStatus);
  }
};

/**
 *
 * @param status
 */
const getNavEntryStyle = (status: string) => {
  switch (status) {
    case "passed":
      return styles.navEntryPassed;

    case "failed":
      return styles.navEntryFailed;

    default:
      return styles.navEntryDefault;
  }
}

const styles = StyleSheet.create({
  buttonsContainer: {
    width: "3em"
  },
  navColumn: {
    height: "100%",
    width: COLWIDTH,
    position: "fixed",
    "z-index": 1,
    "top": 0,
    "left": 0,
    "overflow-x": "hidden",
    padding: "1px",
    background: LIGHT_GREY,
  },
  navLabel: {
    "text-overflow": "ellipsis",
    "white-space": "nowrap",
    fontSize: "small",
    "max-width": "80%",
  },
  runButton: {
    cursor: 'pointer',
    color: 'black',
    'padding-left': '3px',
    'padding-right': '3px',
    transition: 'color 0.3s ease-out 0s',
    ':hover': {
      color: LIGHT_GREY,
    }
  },
  inactiveButton: {
    color: LIGHT_GREY,
    'padding-left': '3px',
    'padding-right': '3px',
  },
  navEntryPassed: { background: "#c0ffbf" },
  navEntryFailed: { background: "#ff7a7a" },
  navEntryDefault: { background: MEDIUM_GREY },
  navEntryCommon: {
    display: "flex",
    "justify-content": "space-between",
    "align-items": "center",
  }
});
